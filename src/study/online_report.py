"""Recompute the solver comparison from literal rollouts and matched development answers."""

from itertools import batched, groupby
from statistics import mean

from .benchmark import population
from .design import GITHUB, PAGES, Run
from .depth_review import compare_training_groups, different_group_credit, effective_bit, numbers
from .domain import Problem
from .exposures import check_exposures
from .learnability_analysis import paired_change
from .learning_review import execute_steps
from .online_evidence import audit_intervention, paired_examples, solver_bit
from .online_solvers import NAMES, ORIGINAL_PAIR, SINGLE
from .online_trajectory import trajectory_evidence, trajectory_note, trajectory_text
from .prompts import messages
from .records import terminal
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
        grade = int(numbers(row["trace"], len(problem.steps))==execute_steps(problem))
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
    changed_groups = 0
    for group in complete:
        if all(len(r["reports"])==3 for r in group):
            j2 = [terminal(r["reports"][1],2) for r in group]
            j3 = [r["reward"] for r in group]
            changed_groups += different_group_credit(j2,j3)
    curves = [dict(step=g[0]["step"]+1, reward=mean(r["reward"] for r in g), exact=mean(r["label"] for r in g)) for g in complete]
    return dict(groups=len(complete), samples=len(samples), reward=sum(r["reward"] for r in samples),
                exact=sum(r["label"] for r in samples), false_accept=sum(r["reward"]>r["label"] for r in samples),
                false_reject=sum(r["reward"]<r["label"] for r in samples),
                mixed=sum(len({r["reward"] for r in g})>1 for g in complete), curves=curves,
                j3_fixed=sum(r["label"]==r["reward"] for r in changes), j3_harmed=sum(r["label"]!=r["reward"] for r in changes),
                changed_advantage_groups=changed_groups)


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
    amended = (root/"one-judge-plan.json").is_file()
    for name in NAMES if amended else ORIGINAL_PAIR:
        folder = root.parent/name
        rollouts = list(rows(folder/"rollouts.jsonl"))
        completed = len(rollouts)//4*4
        probes = [r for r in rows(folder/"metrics.jsonl") if "development_accuracy" in r]
        arms.append(dict(name=name, depth=int(name[-1]), **arm_progress(folder, plan["updates"]),
                         signal=signal(rollouts), probes=probes, latest_group=rollouts[max(0,completed-4):completed]))
    return dict(plan=plan, base=dict(correct=sum(base.values()),n=len(base)), arms=arms,
                comparison=read_json(root/"online-comparison.json", {}),
                three_depths=read_json(root/"three-depth-comparison.json", {}) if amended else {})


def verified_training(folder, depth, keys, identity, updates):
    """Independently match every effective reward to its actual prompt chain and exact arithmetic label."""
    spec = read_json(folder/"recipe.json")
    receipt = read_json(folder/"trained.json")
    confirmed = read_json(folder.parent/"confirm-winner/configuration.json")
    if read_json(folder/"configuration.json") != confirmed:
        raise ValueError("Solver training used a different frozen judge deployment")
    if (spec["initial_adapter_sha256"] != identity or receipt["initial_adapter_sha256"] != identity
        or receipt["updates"] != updates or spec["run"]["initial"] is not None):
        raise ValueError("Solver initialization or completed update count differs")
    calls = {}
    for attempt in sorted((folder/"train").glob("*/calls.jsonl")):
        calls.update((r["id"], r) for r in rows(attempt))
    effective = list(rows(folder/"rollouts.jsonl"))
    optimizer = {r["step"]:r["rewards/registered_reward/mean"] for r in rows(folder/"metrics.jsonl")
                 if "rewards/registered_reward/mean" in r}
    if set(optimizer)!=set(range(1,updates+1)) or any(optimizer[i]!=mean(r["reward"] for r in g)
        for i,g in enumerate(batched(effective,4),1)):
        raise ValueError("TRL's optimizer reward differs from the frozen judge's logged reward")
    for row in effective:
        p, trace, reports = Problem.from_expression(row["expression"]), row["answer"], row["reports"]
        if (p.key in keys or p.key != row["key"] or len(reports)!=depth or row["label"]!=(numbers(trace,len(p.steps))==execute_steps(p))
            or row["reward"]!=solver_bit(reports[-1], depth)):
            raise ValueError(f"Training reward or split mismatch at {row['step']}/{row['sample']}")
        for level, output in enumerate(reports,1):
            call = calls[f"{row['step']}/{row['sample']}/j{level}"]
            if (call["artifact"].split("|")[0]!=confirmed["sha256"] or call["text"] != output or
                call["messages"] != messages(f"j{level}",p,trace,reports[:level-1],"demonstrated")):
                raise ValueError("Training rollout does not match the recorded frozen-judge call")
    return effective


def replay_verdicts(records):
    """Reconstruct both graders' field-four decisions while holding the literal solver answers fixed."""
    summary = dict(n=0, solver=0, j2_correct=0, j3_correct=0, fixed=0, harmed=0)
    for row in records:
        correct = row["valid"]
        second, third = [effective_bit(report) for report in row["reports"][1:]]
        for bit, grade in zip((second, third), row["grades"][1:], strict=True):
            if (bit, bit==correct) != (grade["verdict"], grade["agreement"]):
                raise ValueError("Frozen judge's literal solution verdict differs from the replay grade")
        summary["n"] += 1
        summary["solver"] += correct
        summary["j2_correct"] += second==correct
        summary["j3_correct"] += third==correct
        summary["fixed"] += second!=correct and third==correct
        summary["harmed"] += second==correct and third!=correct
    return summary


def checked_development(folder, keys):
    """Regrade each literal answer and ensure that the audits saw the identical trace in order."""
    score = exact_scores(folder/"solutions.jsonl", keys)
    evaluation = read_json(folder/"development.json")
    if (sum(score.values()),len(score)) != (evaluation["correct"],evaluation["n"]):
        raise ValueError("Final development exact-score receipt differs from the solver outputs")
    replay = read_json(folder/"replay-audit.json")
    if [r["key"] for r in replay] != keys:
        raise ValueError("An audited development solver answer is missing")
    for row, output in zip(replay,rows(folder/"solutions.jsonl"),strict=True):
        if row["trace"]!=output["trace"] or row["valid"]!=score[row["key"]]:
            raise ValueError("Development review supplied a different trace")
    return score, replay


def verify_pair(root):
    """Verify both interventions, held-fixed inputs, raw terminal rewards, and paired endpoint."""
    plan = read_json(root/"new-judges/online-plan.json", {})
    if not plan or not all((root/name/"development.json").is_file() for name in ORIGINAL_PAIR):
        return {}
    profile = read_json(root/"calibrated/profile.json")
    keys = [p.key for p in population(profile,"dev",plan["development_n"])]
    baseline = exact_scores(root/"calibrated/base/replay.jsonl", keys)
    identity = read_json(root/ORIGINAL_PAIR[0]/"recipe.json")["initial_adapter_sha256"]
    signatures = check_exposures(root, [Run(name) for name in ORIGINAL_PAIR])
    trajectories, scores, examples, weights, replays = [], [], [], [], []
    for depth, name in enumerate(ORIGINAL_PAIR, 2):
        folder = root/name
        trajectories.append(verified_training(folder, depth, keys, identity, plan["updates"]))
        score, replay = checked_development(folder, keys)
        weights.append(read_json(folder/"development.json")["weights"])
        replays.append(replay_verdicts(replay))
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
    same = compare_training_groups(*trajectories)
    first = [[r["answer"] for r in arm[:4]] for arm in trajectories]
    comparison = dict(vs_base=[paired_change(s,baseline) for s in scores], d3_minus_d2=difference,
                      initial_adapter_sha256=identity, first_four_answers_matched=first[0]==first[1],
                      final_adapter_sha256=weights, matched_groups=same, development_replays=replays,
                      trajectory=trajectory_evidence(*trajectories),
                      prompt_order_sha256=signatures, examples=cases)
    write_json(root/"new-judges/online-comparison.json", comparison)
    return comparison


def verify_three_depths(root, pair):
    """Extend the checked historical pair using its exact exposures and the new arm's raw records."""
    folder = root/SINGLE
    if not pair or not (root/"new-judges/one-judge-plan.json").is_file() or not (folder/"development.json").is_file():
        return {}
    plan = read_json(root/"new-judges/online-plan.json")
    keys = [p.key for p in population(read_json(root/"calibrated/profile.json"),"dev",plan["development_n"])]
    identity = pair["initial_adapter_sha256"]
    verified_training(folder, 1, keys, identity, plan["updates"])
    digests = check_exposures(root,[Run(name, seed=plan["seed"]) for name in NAMES])
    settings = [read_json(root/name/"recipe.json") for name in NAMES]
    for depth, setting in enumerate(settings,1):
        run = setting["run"]
        expected = dict(settings[0]["run"],name=NAMES[depth-1],reward=f"d{depth}")
        if (run != expected or run["seed"] != plan["seed"] or
            (setting["updates"],setting["group"]) != (plan["updates"],plan["group"])):
            raise ValueError("Unmatched online solver recipes")
    scores = [exact_scores(root/"calibrated/base/replay.jsonl", keys)]
    arms, interventions, cohorts = [], [], []
    for depth,name in enumerate(NAMES,1):
        target = root/name
        score, replay = checked_development(target, keys)
        cohorts.append(replay)
        scores.append(score)
        audit = replay_verdicts(replay)
        direct = [solver_bit(r["reports"][0], 1) for r in replay]
        if any((bit,int(bit==r["valid"])) != (r["grades"][0]["verdict"],r["grades"][0]["agreement"])
               for bit,r in zip(direct,replay,strict=True)):
            raise ValueError("Direct judge verdict differs from its fixed-answer grade")
        cost = read_json(target/"train-cost.json")
        for previous in range(1,depth):
            interventions.append(dict(depth=depth,lower=previous,upper=depth,
                                      **audit_intervention(rows(target/"rollouts.jsonl"),previous,depth)))
        arms.append(dict(depth=depth,**audit,j1_correct=sum(b==r["valid"] for b,r in zip(direct,replay,strict=True)),
                         train_calls=cost["calls"],judge_input_tokens=cost["input_tokens"],judge_output_tokens=cost["output_tokens"],
                         train_seconds=read_json(target/"trained.json")["elapsed_seconds"],
                         final_adapter_sha256=read_json(target/"development.json")["weights"]))
    differences = dict(one_minus_base=paired_change(scores[1],scores[0]),
                       two_minus_one=paired_change(scores[2],scores[1]), three_minus_one=paired_change(scores[3],scores[1]),
                       three_minus_two=pair["d3_minus_d2"])
    result = dict(arms=arms, contrasts=differences, initial_adapter_sha256=identity, prompt_order_sha256=digests,
                  interventions=interventions, examples=paired_examples(cohorts))
    write_json(root/"new-judges/three-depth-comparison.json", result)
    return result


def score_table(study):
    b = study["base"]
    head = ["Solver reward", "Updates", "Groups with mixed rewards", "Exact development solutions"]
    def accuracy(correct, n):
        return f"{correct}/{n} ({100*correct/n:.1f}%)"
    table = [["Starting solver", "0", "—", accuracy(b['correct'],b['n'])]]
    for arm in study["arms"]:
        signal = arm["signal"]
        table.append([f"Frozen Qwen3.5-4B Judge {arm['depth']}", str(arm["updates"]),
                      f"{signal['mixed']}/{signal['groups']}" if signal["groups"] else "—",
                      accuracy(arm['correct'],arm['n']) if arm["n"] else arm["status"]])
    return head,table


def single_contrasts(study):
    """Keep the later-added baseline identifiable alongside the original registered pair."""
    contrasts = study.get("three_depths",{}).get("contrasts",{})
    head = ["Solver comparison", "Gained", "Lost", "Difference (pp)", "Paired 95% interval (pp)"]
    table = []
    for key,label in (("one_minus_base","One minus starting solver"),("two_minus_one","Two minus one"),
                      ("three_minus_one","Three minus one"),("three_minus_two","Three minus two")):
        if key in contrasts:
            change = contrasts[key]
            lo,hi = change["interval"]
            table.append([label, change["fixed"],change["harmed"],f"{100*change['delta']:+.2f}",
                          f"{100*lo:+.1f} to {100*hi:+.1f}"])
    return head,table


def cost_table(complete):
    head = ["Reward depth", "Judge calls", "Judge input tokens", "Judge output tokens", "Training minutes"]
    return head,[[arm["depth"],f"{arm['train_calls']:,}",f"{arm['judge_input_tokens']:,}",
                  f"{arm['judge_output_tokens']:,}", f"{arm['train_seconds']/60:.1f}"] for arm in complete["arms"]]


def intervention_table(complete):
    head = ["Training run", "Verdict comparison", "Fixed", "Introduced errors", "Changed relative credit"]
    return head,[[f"{i['depth']} judges",f"J{i['upper']} vs J{i['lower']}",i["fixed"],i["harmed"],
                  f"{i['changed_credit_groups']}/{i['groups']} groups"] for i in complete["interventions"]]


def conclusion(study):
    c = study.get("comparison", {})
    if not c:
        return "The fresh solvers train on the same arithmetic prompts. Each finished checkpoint is scored on the same development questions as the starting solver."
    effect = c["d3_minus_d2"]
    lo,hi = effect["interval"]
    signal = next(a["signal"] for a in study["arms"] if a["depth"] == 3)
    addition = ""
    if study.get("three_depths"):
        two = study["three_depths"]["contrasts"]["two_minus_one"]
        three = study["three_depths"]["contrasts"]["three_minus_one"]
        addition = (f"Relative to the one-judge solver, two judges changed development accuracy by {100*two['delta']:+.2f} "
                    f"percentage points and three judges by {100*three['delta']:+.2f}. "
                    "The one-judge baseline was registered after both deeper scores were known. ")
    return (addition+f"The three-judge solver changed exact development accuracy by {100*effect['delta']:+.2f} percentage points "
            f"relative to the two-judge solver (paired 95% interval {100*lo:+.1f} to {100*hi:+.1f}). "
            f"It gained {effect['fixed']} solutions and lost {effect['harmed']} on the {effect['n']} shared problems. "
            f"During three-judge training, Judge 3 fixed {signal['j3_fixed']} solution verdicts and introduced "
            f"{signal['j3_harmed']} errors across {signal['samples']:,} sampled answers. Using Judge 3 changed "
            f"the within-group advantages in {signal['changed_advantage_groups']}/{signal['groups']} groups on those same samples. "
            "The interval conditions on these seed-17 checkpoints and the development population. "+
            (trajectory_note(c["trajectory"]) if "trajectory" in c else "")).rstrip()


def online_text(study):
    if not study:
        return ""
    head, table = score_table(study)
    text = ("## Solvers trained with frozen Qwen3.5-4B judges\n\n"+markdown(head, table)+"\n\n"+conclusion(study)+
            f" [Protocol and decoder]({GITHUB}/blob/main/reports/newer-frozen-judges.md#online-solver-comparison) · "
            f"[Rollouts, rewards and exact scores]({GITHUB}/tree/main/results/new-judges).\n\n")
    amended = any(a["depth"] == 1 for a in study["arms"])
    complete = study.get("three_depths",{})
    if amended:
        text += ("The single-judge arm uses Judge 1's first verdict directly. Each additional judge reads the earlier reports. "
                 "Only the solver learns. All runs use matched initialization, seed, prompt order and update budget. "
                 f"[One-judge addendum]({GITHUB}/blob/main/reports/newer-frozen-judges.md#one-judge-baseline-addendum).\n\n")
    if complete:
        text += markdown(*single_contrasts(study))+"\n\nGains and losses compare the same problem across checkpoints. Intervals resample problems within this one seed.\n\n"
    replays = complete.get("arms") or study.get("comparison", {}).get("development_replays", [])
    if replays:
        graders = (["j1_correct"] if complete else []) + ["j2_correct","j3_correct"]
        columns = ["Whose written answers?", "Exact solver answers", *[f"Correct {k[:2].upper()} verdicts" for k in graders], "J3 fixes", "J3 new errors"]
        data = [[f"Solver trained with Judge {r.get('depth',i)}", *(f"{r[k]}/{r['n']}" for k in ("solver",*graders)),
                 r["fixed"],r["harmed"]] for i,r in enumerate(replays, 2)]
        text += ("### Grading each checkpoint's fixed answers\n\n"+markdown(columns,data)+
                 "\n\nA correct verdict accepts correct arithmetic or rejects an arithmetic or format error. "
                 "Changing a verdict in this replay leaves the solver’s written answer fixed.\n\n")
    return text


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


def solver_examples(study):
    complete = study.get("three_depths",{})
    if complete:
        data = [[e["expression"],", ".join(map(str,e["expected"])),
                 *(f"`{t}` ({'correct' if y else 'wrong'})" for t,y in zip(e["traces"],e["correct"],strict=True))]
                for e in complete["examples"]]
        return ("### What each solver wrote on the same calculation\n\n"+
                markdown(["Expression","Exact steps","One-judge solver","Two-judge solver","Three-judge solver"],data)+
                "\n\nEach row is the first development problem with that combination of successes and failures. "
                f"The entries give the predicted first and second step. The explorer shows the literal judge reports "
                f"for every answer in these rows. [Interactive explorer]({PAGES})\n\n")
    examples = study.get("comparison",{}).get("examples",[])
    if not examples:
        return ""
    def show(ex,i):
        j2,j3 = ex["reports"][i][1:]
        return f"`{ex['traces'][i]}` ({'correct' if ex['correct'][i] else 'wrong'}), J2 `{j2}`, J3 `{j3}`"
    data = [[e["expression"], ", ".join(map(str,e["expected"])),show(e,0),show(e,1)] for e in examples]
    return ("### Both solvers on the same development calculation\n\n"+
            markdown(["Expression","Exact steps","Two-judge-trained solver and reviews","Three-judge-trained solver and reviews"],data)+
            "\n\nEach solver writes its answer before grading. In the six-number reviews, the first number audits the preceding judge and the fourth accepts or rejects the solver. The examples take the first problem in each observed pair of outcomes in evaluation order.\n\n")


def fit_results(root):
    from .solver_fit import CANDIDATES, starting_scores
    measured = []
    reference = {}
    for key in CANDIDATES:
        r = read_json(root/key/"result.json")
        if r:
            answers = list(rows(root/key/"starting-answers.jsonl"))
            if answers:
                pool = [Problem.from_expression(row["expression"]) for row in answers]
                counts = starting_scores(pool, answers)
                scores = {p.key:row["correct"] for p,row in zip(pool,answers,strict=True)}
                if len(scores)!=len(pool) or any(r[k]!=v for k,v in counts.items()):
                    raise ValueError(f"Incorrect hardware calibration counts in {key}")
                if key=="original-nf4":
                    reference = scores
                elif len(scores)==len(reference):
                    if list(scores)!=list(reference):
                        raise ValueError("Hardware calibration used different questions or question order")
                    r["paired_vs_nf4"] = paired_change(scores,reference)
            measured.append(dict(key=key, **r))
    return measured


def fit_table(measured):
    head = ["Solver", "Precision", "GPU test", "Parsed", "Exact", "Peak solver allocation"]
    table = []
    for r in measured:
        n = r.get("n")
        peak = r.get("after_step",{}).get("solver_peak_mib")
        table.append([r["model"].split("/")[-1],r["precision"].upper(),r["status"],
                      f"{r['parsed']}/{n}" if n else "—",f"{r['correct']}/{n}" if n else "—",
                      f"{peak:,.0f} MiB" if peak else "—"])
    return head,table


def fit_assessment(measured):
    """Distinguish pre-update calibration, a nonzero optimization signal and sustained learning."""
    notes = []
    for r in measured:
        effect = r.get("paired_vs_nf4")
        if not effect:
            continue
        lo,hi = effect["interval"]
        name = f"{r['model'].split('/')[-1]} at {r['precision'].upper()}"
        notes.append(f"Against the original NF4 solver, {name} gained {effect['fixed']} and lost {effect['harmed']} "
                     f"exact answers on the same {effect['n']} starting prompts. The descriptive paired difference was "
                     f"{100*effect['delta']:+.1f} percentage points (95% resampling interval {100*lo:+.1f} to {100*hi:+.1f}).")
        if r["key"]=="base-2b" and r.get("updates")==1 and (r.get("gradient_norm") or 0)>0:
            notes.append(f"The pretraining-only base model received rewards {r['group_rewards']} and an optimizer gradient "
                         f"norm of {r['gradient_norm']:.4g}. It is the candidate for a future matched comparison starting before RLVR. "
                         "The longer-term effect on solver accuracy remains open.")
    return " ".join(notes)


def fit_text(measured):
    if not measured:
        return ""
    return ("### Solver precision and pretraining-only hardware checks\n\n"+markdown(*fit_table(measured))+
            "\n\nStarting accuracy uses greedy decoding on the same train-split calibration problems before the disposable update. "
            "The 4B judge ran on the same GPU. Peak allocation is PyTorch memory for the solver process alone. "+
            fit_assessment(measured)+
            f" [Hardware protocol]({GITHUB}/blob/main/reports/solver-precision.md) · [Measured costs and outcomes]({GITHUB}/tree/main/results/solver-fit).\n\n")


def fit_pages(measured, destination):
    """Make each hardware observation traceable to its checkpoint, calibration outputs and optimizer log."""
    for r in measured:
        key = r["key"]
        record = f"{GITHUB}/tree/main/results/solver-fit/{key}"
        if "group_rewards" in r:
            bits = ", ".join(map(str, r["group_rewards"]))
            gradient = r.get("gradient_norm")
            value = format(gradient, ".4g") if gradient is not None else "unavailable"
            signal = "equal rewards" if len(set(r["group_rewards"]))==1 else "mixed rewards"
            note = (f"The four rewards were [{bits}]. The optimizer received {signal} and recorded a gradient norm "
                    f"of {value}. One optimizer step measures hardware feasibility. Establishing a learning "
                    f"effect requires repeated updates and a separate evaluation. [Raw measurements]({record}).")
            model_path = f"https://huggingface.co/BurnyCoder/recursive-judge-grpo-adapters/tree/main/runs/solver-fit/{key}"
            note += f" [One-step adapter]({model_path})."
        else:
            note = f"The GPU trial ended with this placement or allocation error. `{r['reason']}` [Device record]({record})."
        title = f"{r['model'].split('/')[-1]} at {r['precision'].upper()}"
        atomic(destination/key/"experiment.md", f"# {title}\n\n"+fit_text([r])+note+"\n")
        atomic(destination/key/"learnings.md", f"# Hardware findings for {title}\n\n"+note+"\n")


def fit_review(root, measured):
    """Expose the actual training group behind each feasibility claim and the paired pre-update evidence."""
    data = []
    for r in measured:
        for sample in rows(root/r["key"]/"rollouts.jsonl"):
            data.append([r["key"],sample["expression"],f"`{sample['answer'].strip()}`",sample["label"],
                         f"`{sample['reports'][-1].strip()}`",sample["reward"]])
    return ("# Review of solver precision and pretrained initialization\n\n"+fit_text(measured)+
            markdown(["Trial","Training problem","Solver wrote","Exact","Judge 3 wrote","Reward"],data)+
            "\n\nThese training examples follow the starting assessment. A nonzero gradient establishes an update signal on that group. "
            "The starting assessment supplies no estimate of post-training accuracy. Published trial adapters and device readings accompany each result. "
            f"[Source artifacts]({GITHUB}/tree/main/results/solver-fit).\n")


def paired_review(study):
    """Expose the initial-weight and exposure checks and every paired change, including negative results."""
    c=study.get("comparison",{})
    if not c:
        return ""
    data=[]
    for label, change in zip(("Two judges minus starting solver","Three judges minus starting solver","Three minus two"),
                             [*c["vs_base"],c["d3_minus_d2"]],strict=True):
        lo,hi=change["interval"]
        data.append([label,change["n"],change["fixed"],change["harmed"],f"{100*change['delta']:+.2f}",
                     f"{100*lo:+.1f} to {100*hi:+.1f}"])
    provenance=(f"The two fresh adapters had the same initial SHA-256 `{c['initial_adapter_sha256']}`. The actual prompt-order digest "
                f"for both training trajectories was `{next(iter(c['prompt_order_sha256'].values()))}`. "
                f"The first four sampled answers {'matched' if c['first_four_answers_matched'] else 'differed'}. "
                f"Both arms produced the same four answers and lower reports on {len(c['matched_groups']['matched'])} whole groups. Of these, "
                f"{len(c['matched_groups']['different_credits'])} received different group-relative credit. "
                "Each effective training reward was recomputed from the raw terminal report and checked against its exact prompt history and the reward mean TRL logged for the optimizer. "
                "Every finished checkpoint contributed one greedy trace per development problem. The training and development IDs were disjoint.")
    supplement = ""
    complete = study.get("three_depths",{})
    if complete:
        supplement = ("\n\n## Direct and recursive rewards on the same live answers\n\n"+
                      markdown(*intervention_table(complete))+
                      "\n\nEvery comparison uses the lower and upper reports from the same training run. "
                      "A fix or an introduced error counts one answer. A change in relative credit counts one "
                      "four-answer group. The saved training traces support this substitution without another model call.\n\n"+
                      markdown(*cost_table(complete))+
                      "\n\nThe durations are trainer wall time, including reward generation and periodic probes. "
                      f"[Call timings, GPU engine counters and solver CUDA events]({GITHUB}/tree/main/results/new-judges).\n")
    return ("# Independent review of the Qwen3.5-4B solver-reward comparison\n\n"+online_text(study)+
            markdown(["Paired comparison","Problems","Gained","Lost","Difference (pp)","95% interval (pp)"],data)+
            "\n\n"+provenance+supplement+"\n\n"+trajectory_text(c.get("trajectory"))+solver_examples(study))


def plot_online(study, path):
    """Plot only completed checkpoints, with the original solver and the realized reward signal explicitly labeled."""
    completed = [a for a in study.get("arms",[]) if a["n"]]
    if not completed:
        path.unlink(missing_ok=True)
        return
    import matplotlib.pyplot as plt
    fig,axes = plt.subplots(1,2,figsize=(10,3.8),layout="constrained")
    base=study["base"]
    def bars(ax, labels, pairs, colors, title):
        scales=[100*x/n for x,n in pairs]
        rectangles=ax.bar(labels,scales,color=colors)
        ax.set(ylim=(0,110),ylabel="Percent", title=title,yticks=[0,25,50,75,100])
        ax.bar_label(rectangles,labels=[f"{x}/{n}" for x,n in pairs],padding=3)
        ax.spines[["top","right"]].set_visible(False)
    labels=["1 judge" if a["depth"]==1 else f"{a['depth']} judges" for a in completed]
    colors=[{1:"#ab692b",2:"#24796c",3:"#4776ad"}[a["depth"]] for a in completed]
    bars(axes[0],["Starting solver",*labels],[(base["correct"],base["n"]),*((a["correct"],a["n"]) for a in completed)],
         ["#72807f",*colors],"Exact development solutions")
    bars(axes[1],labels,[(a["signal"]["mixed"],a["signal"]["groups"]) for a in completed],colors,
         "Training groups with mixed rewards")
    fig.suptitle("Training Qwen2.5-1.5B with frozen Qwen3.5-4B judges")
    fig.savefig(path,dpi=150)
    plt.close(fig)
