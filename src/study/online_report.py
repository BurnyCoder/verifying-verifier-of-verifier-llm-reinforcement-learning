"""Recompute the solver comparison from literal rollouts and matched development answers."""

from itertools import groupby
from statistics import mean

from .benchmark import population
from .design import GITHUB, Run
from .domain import Problem
from .exposures import check_exposures
from .learnability_analysis import paired_change
from .online_solvers import NAMES
from .prompts import messages
from .records import solver_truth, terminal
from .storage import atomic, read_json, rows, write_json
from .tables import markdown


def exact_scores(path, keys):
    """Re-execute each prediction, require exactly one answer per canonical development problem."""
    data = list(rows(path))
    if [r["key"] for r in data] != keys or len(set(keys)) != len(keys):
        raise ValueError(f"Development IDs or order do not match at {path}")
    scores = {}
    for row in data:
        problem = Problem.from_expression(row["expression"])
        grade = solver_truth(problem, row["trace"])[0]
        if problem.key != row["key"] or grade != row["correct"]:
            raise ValueError(f"Stored exact score differs for {row['key']}")
        scores[problem.key] = grade
    return scores


def signal(rollouts):
    """Describe GRPO signal on the actual four samples from each completed group."""
    clusters = [list(g) for _,g in groupby(rollouts, key=lambda r:r["step"])]
    complete = [g for g in clusters if len(g)==4]
    samples = [r for g in complete for r in g]
    changes = [r for r in samples if len(r["reports"])==3 and terminal(r["reports"][1],2)!=r["reward"]]
    curves = [dict(step=g[0]["step"]+1, reward=mean(r["reward"] for r in g), exact=mean(r["label"] for r in g)) for g in complete]
    return dict(groups=len(complete), samples=len(samples), reward=sum(r["reward"] for r in samples),
                exact=sum(r["label"] for r in samples), false_accept=sum(r["reward"]>r["label"] for r in samples),
                false_reject=sum(r["reward"]<r["label"] for r in samples),
                mixed=sum(len({r["reward"] for r in g})>1 for g in complete), curves=curves,
                j3_fixed=sum(r["label"]==r["reward"] for r in changes), j3_harmed=sum(r["label"]!=r["reward"] for r in changes))


def arm_progress(folder, target):
    """Use completed optimizer callbacks for progress and a finished development receipt for accuracy."""
    dev = read_json(folder/"development.json", {})
    trained = read_json(folder/"trained.json", {})
    cost = next(reversed(list(rows(folder/"cost.jsonl"))), {})
    done = trained.get("updates", cost.get("step", 0))
    status = ("Evaluated" if dev else "Trained" if trained else f"Training · {done}/{target}"
              if (folder/"recipe.json").exists() else "Scheduled")
    return dict(status=status, updates=done, n=dev.get("n"), correct=dev.get("correct"),
                elapsed_seconds=trained.get("elapsed_seconds", cost.get("elapsed_seconds")))


def collect_online(root):
    plan = read_json(root/"online-plan.json")
    if not plan:
        return {}
    profile = read_json(root.parent/"calibrated/profile.json")
    keys = [p.key for p in population(profile, "dev", plan["development_n"])]
    base = exact_scores(root.parent/"calibrated/base/replay.jsonl", keys)
    arms = []
    for name in NAMES:
        folder = root.parent/name
        probes = [r for r in rows(folder/"metrics.jsonl") if "development_accuracy" in r]
        arms.append(dict(name=name, depth=int(name[-1]), **arm_progress(folder, plan["updates"]),
                         signal=signal(rows(folder/"rollouts.jsonl")), probes=probes))
    return dict(plan=plan, base=dict(correct=sum(base.values()),n=len(base)), arms=arms,
                comparison=read_json(root/"online-comparison.json", {}))


def verified_training(folder, depth, keys, identity, updates):
    """Independently match every effective reward to its actual prompt chain and exact arithmetic label."""
    spec = read_json(folder/"recipe.json")
    receipt = read_json(folder/"trained.json")
    if (spec["initial_adapter_sha256"] != identity or receipt["initial_adapter_sha256"] != identity
        or receipt["updates"] != updates or spec["run"]["initial"] is not None):
        raise ValueError("Solver initialization or completed update count differs")
    calls = {}
    for attempt in sorted((folder/"train").glob("*/calls.jsonl")):
        calls.update((r["id"], r) for r in rows(attempt))
    effective = list(rows(folder/"rollouts.jsonl"))
    for row in effective:
        p, trace, reports = Problem.from_expression(row["expression"]), row["answer"], row["reports"]
        if (p.key in keys or p.key != row["key"] or len(reports)!=depth or row["label"]!=solver_truth(p,trace)[0]
            or row["reward"]!=terminal(reports[-1],depth)):
            raise ValueError(f"Training reward or split mismatch at {row['step']}/{row['sample']}")
        for level, output in enumerate(reports,1):
            call = calls[f"{row['step']}/{row['sample']}/j{level}"]
            if call["text"] != output or call["messages"] != messages(f"j{level}",p,trace,reports[:level-1],"demonstrated"):
                raise ValueError("Training rollout does not match the recorded frozen-judge call")
    return [r["answer"] for r in effective[:4]]


def verify_pair(root):
    """Verify both interventions, held-fixed inputs, raw terminal rewards, and paired endpoint."""
    plan = read_json(root/"new-judges/online-plan.json", {})
    if not plan or not all((root/name/"development.json").is_file() for name in NAMES):
        return {}
    profile = read_json(root/"calibrated/profile.json")
    keys = [p.key for p in population(profile,"dev",plan["development_n"])]
    baseline = exact_scores(root/"calibrated/base/replay.jsonl", keys)
    identity = read_json(root/NAMES[0]/"recipe.json")["initial_adapter_sha256"]
    signatures = check_exposures(root, [Run(name) for name in NAMES])
    first, scores, examples = [], [], []
    for depth, name in enumerate(NAMES, 2):
        folder = root/name
        first.append(verified_training(folder, depth, keys, identity, plan["updates"]))
        score = exact_scores(folder/"solutions.jsonl", keys)
        if sum(score.values()) != read_json(folder/"development.json")["correct"]:
            raise ValueError("Final development exact-score receipt differs from the solver outputs")
        # Verify the full frozen chain on both checkpoints' literal development answers.
        replay = read_json(folder/"replay-audit.json")
        if [r["key"] for r in replay] != keys:
            raise ValueError("An audited development solver answer is missing")
        for row, output in zip(replay,rows(folder/"solutions.jsonl"),strict=True):
            if row["trace"]!=output["trace"] or row["valid"]!=score[row["key"]]:
                raise ValueError("Development review supplied a different trace")
        scores.append(score)
        examples.append({r["key"]:r for r in replay})
    a,b = scores
    difference = paired_change(b,a)
    cases = []
    for x,y in ((1,0),(0,1),(1,1),(0,0)):
        key = next((k for k in keys if (a[k],b[k])==(x,y)),None)
        if key:
            p = Problem.from_expression(examples[0][key]["expression"])
            cases.append(dict(key=key, expression=p.expression, expected=list(p.values),
                traces=[e[key]["trace"] for e in examples], reports=[e[key]["reports"] for e in examples], correct=[x,y]))
    comparison = dict(vs_base=[paired_change(s,baseline) for s in scores], d3_minus_d2=difference,
                      initial_adapter_sha256=identity, first_four_answers_matched=first[0]==first[1],
                      prompt_order_sha256=signatures, examples=cases)
    write_json(root/"new-judges/online-comparison.json", comparison)
    return comparison


def score_table(study):
    b = study["base"]
    head = ["Solver reward", "Updates", "Groups with mixed rewards", "Exact development solutions"]
    table = [["Starting solver", "0", "—", f"{b['correct']}/{b['n']}"]]
    for arm in study["arms"]:
        signal = arm["signal"]
        table.append([f"Frozen Qwen3.5-4B Judge {arm['depth']}", str(arm["updates"]),
                      f"{signal['mixed']}/{signal['groups']}" if signal["groups"] else "—",
                      f"{arm['correct']}/{arm['n']}" if arm["n"] else arm["status"]])
    return head,table


def conclusion(study):
    c = study.get("comparison", {})
    if not c:
        return "The fresh solvers train on the same arithmetic prompts. Each finished checkpoint is scored on the same development questions as the starting solver."
    effect = c["d3_minus_d2"]
    lo,hi = effect["interval"]
    signal = study["arms"][1]["signal"]
    return (f"The three-judge solver changed exact development accuracy by {100*effect['delta']:+.1f} percentage points "
            f"relative to the two-judge solver (paired 95% interval {100*lo:+.1f} to {100*hi:+.1f}). "
            f"It gained {effect['fixed']} solutions and lost {effect['harmed']} on the {effect['n']} shared problems. "
            f"During three-judge training, Judge 3 fixed {signal['j3_fixed']} solution verdicts and introduced "
            f"{signal['j3_harmed']} errors across {signal['samples']:,} sampled answers. "
            "The interval conditions on these seed-17 checkpoints and the development population.")


def online_text(study):
    if not study:
        return ""
    head, table = score_table(study)
    return ("## Solvers trained with frozen Qwen3.5-4B judges\n\n"+markdown(head, table)+"\n\n"+conclusion(study)+
            f" [Protocol and decoder]({GITHUB}/blob/main/reports/newer-frozen-judges.md#online-solver-comparison) · "
            f"[Rollouts, rewards and exact scores]({GITHUB}/tree/main/results/new-judges).\n\n")


def experiment_pages(study, destination):
    if not study:
        return
    for arm in study["arms"]:
        name, s = arm["name"], arm["signal"]
        target = destination/name.split("/")[-1]
        note = (f"The exact checker accepted {s['exact']}/{s['samples']} training answers. The reward accepted "
                f"{s['reward']}/{s['samples']}, including {s['false_accept']} incorrect answers. It rejected "
                f"{s['false_reject']} correct answers. {s['mixed']} of {s['groups']} groups supplied mixed rewards."
                if s["samples"] else "No complete training group has been recorded.")
        link = f"[Raw solver and judge outputs]({GITHUB}/tree/main/results/{name})"
        atomic(target/"experiment.md", f"# Fresh solver with frozen Judge {arm['depth']}\n\n"+online_text(study)+note+" "+link+"\n")
        atomic(target/"learnings.md", f"# Training signal from frozen Judge {arm['depth']}\n\n"+note+" "+link+"\n")
