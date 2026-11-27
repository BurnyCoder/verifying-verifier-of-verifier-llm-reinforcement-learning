"""Audit the observed depth gap on training and development data, independently of the reward callback."""

import operator
import re
from collections import Counter
from itertools import batched, combinations

from .design import SEEDS
from .domain import Problem
from .learning_review import execute_steps
from .storage import read_json, rows
from .tables import markdown


def numbers(text, width):
    """Reconstruct the registered output grammar by checking each field separately."""
    text = text.strip()
    if text.startswith("[") and text.endswith("]"):
        text = text[1:-1].strip()
    fields = [part.strip() for part in text.split(",")]
    if len(text) <= 1024 and len(fields) == width and all(re.fullmatch(r"[+-]?[0-9]{1,14}", part) for part in fields):
        return tuple(map(int, fields))
    return None


def effective_bit(text):
    """Higher-order reports give the solver credit through field four when the audit flag is binary."""
    record = numbers(text, 6)
    return int(record is not None and record[0] in (0, 1) and record[3] == 1)


def trace_error(problem, answer):
    """For the calibrated two-add family, test step two against the solver's own first value."""
    truth = execute_steps(problem)
    proposed = numbers(answer, 2)
    if proposed is None:
        return "format"
    if proposed == truth:
        return "correct"
    if proposed[0] == truth[0]:
        return "second wrong"
    _, _, left, sign, right = problem.steps[1].split()
    if left != "s1" or sign not in ("+", "-"):
        raise ValueError("This diagnostic requires the registered two-add layout")
    implied = {"+": operator.add, "-": operator.sub}[sign](proposed[0], int(right))
    return "first wrong, second consistent" if proposed[1] == implied else "first wrong, second inconsistent"


def group_evidence(deep):
    """Replay both reward rules on identical samples, preserving the four-way GRPO groups."""
    fixes = harms = changed = 0
    preferences = [Counter(), Counter()]
    for group in batched(deep, 4):
        if len(group) != 4:
            raise ValueError("A comparison requires four samples per group")
        labels = [r["label"] for r in group]
        second, third = [[effective_bit(r["reports"][index]) for r in group] for index in (1, 2)]
        fixes += sum(a != y and b == y for a, b, y in zip(second, third, labels, strict=True))
        harms += sum(a == y and b != y for a, b, y in zip(second, third, labels, strict=True))
        # Centered binary returns induce the same normalized advantages if both vectors are constant.
        changed += second != third and (len(set(second)) > 1 or len(set(third)) > 1)
        for i, j in combinations(range(4), 2):
            if labels[i] == labels[j]:
                continue
            good, bad = (i, j) if labels[i] else (j, i)
            for counts, votes in zip(preferences, (second, third), strict=True):
                counts[votes[good] - votes[bad]] += 1
    return dict(fixes=fixes, harms=harms, changed_groups=changed,
                j2_pairs=[preferences[0][i] for i in (1, 0, -1)], j3_pairs=[preferences[1][i] for i in (1, 0, -1)])


def audit_arm(directory, depth):
    """Cross-check actual responses, arithmetic, effective rewards, grouping and TRL's optimizer telemetry."""
    training = list(rows(directory/"rollouts.jsonl"))
    dev = list(rows(directory/"replay.jsonl"))
    updates = read_json(directory/"trained.json")["updates"]
    logs = {r["step"]: r["rewards/registered_reward/mean"] for r in rows(directory/"metrics.jsonl")
            if "rewards/registered_reward/mean" in r}
    if len(training) != 4*updates or set(logs) != set(range(1, updates+1)):
        raise ValueError(f"Incomplete optimizer observations in {directory.name}")
    parts, paid, cases = Counter(), Counter(), Counter()
    for step, group in enumerate(batched(training, 4)):
        if (len({r["key"] for r in group}) != 1 or
                [(r["step"], r["sample"]) for r in group] != [(step, s) for s in range(4)]):
            raise ValueError(f"Unexpected training order in {directory.name}")
        p = Problem.from_expression(group[0]["expression"])
        for r in group:
            kind = trace_error(p, r["answer"])
            if (r["key"] != p.key or r["expression"] != p.expression or len(r["reports"]) != depth or
                    r["label"] != (kind == "correct") or r["reward"] != effective_bit(r["reports"][-1])):
                raise ValueError(f"Training grade or routing mismatch in {directory.name}")
            parts[kind] += 1
            paid[kind] += r["reward"]
        if sum(r["reward"] for r in group)/4 != logs[step+1]:
            raise ValueError(f"Trainer mean reward mismatch at {directory.name} update {step+1}")
    for r in dev:
        p = Problem.from_expression(r["expression"])
        kind = trace_error(p, r["trace"])
        if (r["key"] != p.key or list(p.steps) != r["problem"] or list(execute_steps(p)) != r["expected_values"] or
                r["correct"] != (kind == "correct") or r["malformed"] != (kind == "format")):
            raise ValueError(f"Development arithmetic or parse mismatch in {directory.name}")
        cases[kind] += 1
    windows = [[sum(r[k] for r in quarter) for k in ("label", "reward")]
               for quarter in (training[:updates], training[-updates:])]
    return training, dev, dict(training=parts, rewarded=paid, dev=cases, first_quarter=windows[0], last_quarter=windows[1])


def audited_seed(directory, seed):
    """Read both completed reward treatments. No held-out record is used by this diagnostic."""
    paths = [directory/f"d{depth}-{seed}" for depth in (2, 3)]
    if not all((path/"development.json").is_file() for path in paths):
        return None
    shallow, dev2, stats2 = audit_arm(paths[0], 2)
    deep, dev3, stats3 = audit_arm(paths[1], 3)
    if ([r["key"] for r in shallow] != [r["key"] for r in deep] or
            [r["key"] for r in dev2] != [r["key"] for r in dev3] or len({r["key"] for r in dev3}) != len(dev3)):
        raise ValueError("The depth comparison requires the same problems in the same order")
    transitions = []
    accepted, agreement = [0, 0], [0, 0]
    shared_error = None
    paired = Counter()
    for a, b in zip(dev2, dev3, strict=True):
        verdicts = [effective_bit(b["reports"][i]) for i in (1, 2)]
        if verdicts != b["verdicts"][1:]:
            raise ValueError("The fixed-answer replay disagrees with the logged verdicts")
        for i, bit in enumerate(verdicts):
            accepted[i] += bit
            agreement[i] += bit == b["correct"]
        outcome = "both" if a["correct"] and b["correct"] else "two only" if a["correct"] else "three only" if b["correct"] else "neither"
        paired[outcome] += 1
        if verdicts[0] != verdicts[1]:
            transitions.append(dict(expression=b["expression"], output=b["trace"], truth=b["expected_values"],
                                    bits=verdicts, reports=b["reports"][1:], correct=b["correct"]))
        if shared_error is None and a["correct"] and not b["correct"] and not b["malformed"] and b["verdicts"] == [1,1,1]:
            shared_error = dict(expression=b["expression"], right=a["trace"], wrong=b["trace"])
    return dict(seed=seed, n=len(deep), groups=len(deep)//4, dev_n=len(dev3), two=stats2, three=stats3,
                paired=paired, accepted=accepted, agreement=agreement, transitions=transitions, shared_error=shared_error,
                transcript_audit=read_json(directory/"diagnostics"/f"depth-transcripts-{seed}.json"), **group_evidence(deep))


def readme_depth(data):
    """Keep the original seed's worked examples visible as later replications arrive."""
    reviews = data["depth_review"]
    if not reviews:
        return ""
    r = reviews[0]
    seed, n, deep = r["seed"], r["dev_n"], r["three"]
    correct, two_correct = deep["dev"]["correct"], r["two"]["dev"]["correct"]
    paired = r["paired"]
    measured = {row["name"]: row for row in data["runs"] if row["completed_development"]}
    def dev_score(key):
        x = measured[key]
        return f"{x['dev_correct_n']}/{x['dev_n']}"
    sections = ["## Why did the two-judge and three-judge solvers diverge?",
        f"**With seed {seed}, training the solver with two frozen judges gave {two_correct}/{n} correct "
        f"solutions ({100*two_correct/n:.1f}%). Training it with three gave {correct}/{n} ({100*correct/n:.1f}%).** "
        f"The gap was {abs(correct-two_correct)} complete solutions ({100*(correct-two_correct)/n:+.2f} percentage points, three minus two). "
        f"Both solvers started from the same model and saw the same problems in the same order. An integer program "
        f"graded every intermediate step. On the paired problems, only the two-judge solver was correct on "
        f"{paired['two only']}, only the three-judge solver on {paired['three only']}, both on {paired['both']}, "
        f"and neither on {paired['neither']}. These are development results on the calibrated arithmetic benchmark."]
    reference = [(key, label) for key, label in (("base","the starting solver"),(f"d1-{seed}","one judge"),
                 (f"flat-{seed}","three independent votes"),(f"oracle-{seed}","the exact checker"),
                 (f"hybrid-{seed}","the third judge gated by the exact checker"),(f"shuffle-{seed}","shuffled three-judge rewards"))
                 if key in measured]
    if reference:
        sections.append("The same evaluation gave "+", ".join(f"{dev_score(key)} for {label}" for key,label in reference)+".")
    fixed = sum(e["bits"][1] == e["correct"] for e in r["transitions"])
    sections += ["### What happens if we stop at Judge 2 on the same answers?",
        f"The three-judge-trained solver still solved **{correct}/{n}**. Its written answers were already fixed "
        f"before grading. On those answers, Judge 3 changed {len(r['transitions'])} of Judge 2’s verdicts. "
        f"It corrected {fixed} and wrongly overturned {len(r['transitions'])-fixed}.",
        markdown(["Stopping point on the fixed answers", "Answers approved", "Verdicts agreeing with the checker"],
                 [[f"Judge {i+2}",f"{r['accepted'][i]}/{n}",f"{r['agreement'][i]}/{n}"] for i in range(2)])]
    if r["transitions"]:
        example_rows = []
        for e in r["transitions"]:
            decisions = []
            for bit, report in zip(e["bits"],e["reports"],strict=True):
                record = numbers(report,6)
                detail = ""
                if record and record[0] not in (0,1):
                    detail = f" (invalid audit flag {record[0]})"
                decisions.append(("Accepted" if bit else "Rejected")+detail)
            example_rows.append([e["expression"],e["output"].replace("\n"," "),",".join(map(str,e["truth"])),*decisions])
        sections += ["Every changed development verdict appears here.",
                     markdown(["Problem","Submitted steps","Correct steps","Judge 2","Judge 3"],example_rows)]
    if r["shared_error"]:
        e = r["shared_error"]
        sections.append(f"On `{e['expression']}`, the two-judge-trained solver wrote `{e['right']}`. The three-judge-trained "
                        f"solver wrote `{e['wrong']}`, and all three judges approved it in the replay.")
    valid = deep["training"]["correct"]
    wrong = r["n"]-valid
    valid_paid = deep["rewarded"]["correct"]
    wrong_paid = sum(deep["rewarded"].values())-valid_paid
    sections += ["### What changed during training?",
        f"On the same {r['n']:,} training answers sampled by the three-judge solver, Judge 3 fixed {r['fixes']} "
        f"of Judge 2’s verdicts and spoiled {r['harms']}. Substituting Judge 2’s reward would have changed the "
        f"relative credits in **{r['changed_groups']}/{r['groups']} optimizer updates**. "
        "Each GRPO update compares four answers to one question. When gradings change early on, the solvers can "
        "learn different answers and receive different training data at subsequent updates. "
        "[GRPO advantage calculation](https://huggingface.co/docs/trl/grpo_trainer#computing-the-advantage)",
        f"Judge 3 rewarded **{wrong_paid}/{wrong} incorrect answers ({100*wrong_paid/wrong:.1f}%)** and "
        f"**{valid_paid}/{valid} correct answers ({100*valid_paid/valid:.1f}%)**." if valid and wrong else
        f"Judge 3 rewarded {wrong_paid}/{wrong} incorrect and {valid_paid}/{valid} correct answers.",
        markdown(["Within the same training question", "Correct answer ranks higher", "Tied", "Wrong answer ranks higher"],
                 [["Judge 2 on those answers",*r["j2_pairs"]],["Judge 3 on those answers",*r["j3_pairs"]]]),
        f"In its first quarter of training, the three-judge solver produced {deep['first_quarter'][0]} correct "
        f"answers per {r['groups']} samples and received {deep['first_quarter'][1]} positive rewards. In the last "
        f"quarter it produced {deep['last_quarter'][0]} correct answers and received {deep['last_quarter'][1]} positive rewards."]
    local = "first wrong, second consistent"
    bad_first = deep["dev"][local]+deep["dev"]["first wrong, second inconsistent"]
    sections.append(f"The two-judge solver gave the correct first value on {two_correct+r['two']['dev']['second wrong']}/{n} "
                    f"development problems. The three-judge solver gave a wrong first value on {bad_first} and a malformed "
                    f"answer on {deep['dev']['format']}. In {deep['dev'][local]} cases it applied the second operation "
                    f"correctly to its own wrong intermediate value. Judge 3 rewarded {deep['rewarded'][local]}/{deep['training'][local]} "
                    "training answers with that error pattern.")
    verified = r["transcript_audit"]
    checks = (f"The audit independently regraded {2*r['n']:,} training answers and {2*n} development answers, checked "
              "the effective solution-verdict field against each assigned reward, and matched every group mean to TRL’s "
              "optimizer log.")
    if verified:
        calls = sum(s["matched_calls"] for s in verified["arms"].values())
        checks += (f" Prompts and outputs matched the training records for all {calls:,} calls, including the "
                   f"solver answer and preceding reports shown to each judge. Both evaluated adapter hashes matched the saved weights. "
                   f"[Transcript and weight checks](results/calibrated/diagnostics/depth-transcripts-{seed}.json)")
    sections += ["### Could a code bug or a training seed explain it?", checks,
                 "These checks support a training-signal explanation. The three-judge reward frequently approved "
                 "incorrect arithmetic and gave little preference to correct answers within a question. The checker-gated "
                 "control shows that this solver can learn with the same three judge calls when incorrect solutions receive "
                 "zero reward. The depth analysis is exploratory. The contribution of a particular stochastic update "
                 "cannot be identified from these trajectories."]
    if len(reviews)>1:
        sections += ["The same development diagnostic applied to subsequent matched seeds gave these results.",
                     markdown(["Seed", "Two-judge solver exact", "Three-judge solver exact", "J3 fixes on training answers", "J3 harms"],
                              [[e["seed"],f"{e['two']['dev']['correct']}/{e['dev_n']}",f"{e['three']['dev']['correct']}/{e['dev_n']}",
                                e["fixes"],e["harms"]] for e in reviews])]
    base = measured.get("base")
    if base and base["replay"] and base["dev_n"]:
        methods = base["replay"]
        agreements = [m["n"]-m["false_accept"]-m["false_reject"] for m in methods]
        sections += ["### Did Judge 3 actually audit the preceding review?",
            f"On a separate replay of the starting solver’s {base['dev_n']} development responses, Judges 1, 2 and 3 "
            f"agreed with the arithmetic checker on {agreements[0]}, {agreements[1]} and {agreements[2]} verdicts, "
            f"respectively. Three independent first-order votes agreed on {agreements[3]}. On these fixed starting "
            f"responses Judge 3 repaired {base['fixed']} earlier verdicts and overturned {base['harmed']} correct ones."]
        tests = []
        for label,key in (("Frozen","base"),("Trained on exact labels","exact-j3"),
                          ("Alternating, exact route","alt-exact-j3"),("Alternating, top-down route","alt-top-j3")):
            row = measured.get(key)
            if row and row["twins_n"]:
                v = row["evidence_fields"]["visible"]
                split = "Development" if row["twin_split"] == "dev" else "Held out"
                tests.append([label,split,f"{v['solution_bit']}/{v['reports']}",
                              f"{v['localized_and_repaired']}/{v['faults']}",
                              f"{round(row['twins']*row['twins_n'])}/{row['twins_n']}",
                              f"{round(row['masked']*row['twins_n'])}/{row['twins_n']}"])
        if tests:
            sections += ["The paired audit changes a numerical claim in Judge 2’s report while preserving the verdict "
                         "on the solver. To pass a pair, Judge 3 must endorse the sound report and reject the altered "
                         "one with the correct location, replacement and solution verdict.",
                         markdown(["Judge 3","Cohort","Correct solver verdict","Altered review located and repaired",
                                   "Whole pairs correct","Whole pairs with evidence masked"],tests)]
    prefixes = []
    for route,label in (("exact","Exact verdict and evidence"),("top","Top-down learned supervision")):
        arms = [f"{route}-prefix{i}" for i in (1,2,3)]
        if all(a in measured for a in arms):
            prefixes.append([label,*map(dev_score,arms)])
    if prefixes:
        sections += ["A separate experiment keeps **all three judge calls** and varies which reviewers had already "
                     "been trained before a fresh solver learned. These development scores are exact solver solutions.",
                     markdown(["Judge supervision","Only Judge 1 trained","Judges 1 and 2 trained","All three trained"],prefixes)]
    primary = data["primary"]
    inference = ("The preregistered three-seed comparison on 2,048 unseen problems is pending." if "delta" not in primary
                 else f"The registered held-out difference (three minus two) was {100*primary['delta']:+.2f} percentage "
                 f"points, with a paired 95% interval from {100*primary['ci'][0]:+.2f} to {100*primary['ci'][1]:+.2f} "
                 "conditional on these checkpoints.")
    sections.append(inference+" [Raw training and development audit](reports/reviews/depth-diagnosis.md) · "
                    "[Preregistration and decision rule](reports/preregistration.md)")
    return "\n\n".join(sections)+"\n\n"


def collect_depth_review(directory, profile):
    if profile.get("family") != "two-add":
        return []
    return [result for seed in SEEDS if (result := audited_seed(directory, seed))]


def review_text(reviews):
    """Make the causal distinction explicit and label the observed-sample analysis as exploratory."""
    sections = ["# What changed when the solver trained with a third judge?",
                "This exploratory analysis began after observing the seed-17 development gap. The arithmetic grader "
                "executes the numbered operations. The routing check reconstructs the solver verdict from the raw "
                "fourth field of each final report and checks each group against TRL’s own optimizer log. "
                "A nonbinary audit flag or an unparseable report yields a rejection. "
                "[Analysis code](../../src/study/depth_review.py) · [GRPO group advantages](https://huggingface.co/docs/trl/grpo_trainer#computing-the-advantage)"]
    for r in reviews:
        seed, deep = r["seed"], r["three"]
        sections.extend([f"## Seed {seed}",
            f"On {r['dev_n']} matched development problems the two-judge solver alone was correct on "
            f"{r['paired']['two only']}, the three-judge solver alone on {r['paired']['three only']}, both on "
            f"{r['paired']['both']}, and neither on {r['paired']['neither']}. Holding the three-judge solver's outputs "
            f"fixed, Judge 2 accepted {r['accepted'][0]} and Judge 3 accepted {r['accepted'][1]}.",
            markdown(["Three-judge solver error", "Development answers", "Training answers", "Training answers rewarded"],
                     [[k,deep["dev"][k],deep["training"][k],deep["rewarded"][k]] for k in
                      ("correct","first wrong, second consistent","first wrong, second inconsistent","second wrong","format")]),
            f"On the same {r['n']} training answers, Judge 3 fixed {r['fixes']} effective Judge 2 verdicts and "
            f"spoiled {r['harms']}. Its decision changed the within-group advantages in {r['changed_groups']}/{r['groups']} "
            "optimizer updates. Each row below compares correct and incorrect completions of the same question. "
            "Pairs within and across rows share observations.",
            markdown(["Reward applied to these answers", "Correct ranks higher", "Tied", "Incorrect ranks higher"],
                     [["Judge 2",*r["j2_pairs"]],["Judge 3",*r["j3_pairs"]]]),
            markdown(["Training run and window", "Correct", "Rewarded", "Sampled"],
                     [[role+" / "+label, *r[key][window], r["groups"]] for role,key in (("Two judges","two"),("Three judges","three"))
                      for label,window in (("first quarter","first_quarter"),("last quarter","last_quarter"))])])
        if r["transitions"]:
            sections.extend(["Every development verdict change on the three-judge solver’s fixed responses is shown below.",
                markdown(["Expression", "Solver", "Exact values", "Judge 2 report", "Judge 3 report", "Verdict change"],
                         [[e["expression"],e["output"].replace("\n"," "),",".join(map(str,e["truth"])), *e["reports"],
                           "Fixed" if e["bits"][1] == e["correct"] else "Introduced error"] for e in r["transitions"]])])
        sections.append(f"[Two-judge records](../../results/calibrated/d2-{seed}) · [Three-judge records](../../results/calibrated/d3-{seed})")
    sections.append("These comparisons distinguish a change of verdict on an already written answer from a change "
                    "to the solver learned over successive updates. Replacing the reward in an archived group reveals "
                    "which relative credits would change on those samples. A separately trained solver generates its "
                    "own subsequent samples. The checker-gated and shuffled arms test sensitivity to reward quality. "
                    "The registered effectiveness claim uses unseen problems and multiple training seeds. "
                    "[Protocol](../preregistration.md) · [All training arms](../summary.md)")
    return "\n\n".join(sections)+"\n"
