"""Audit the observed depth gap on training and development data, independently of the reward callback."""

import operator
import re
from collections import Counter
from itertools import batched, combinations

from .design import SEEDS
from .domain import Problem
from .learning_review import execute_steps
from .paired_examples import differing_examples, explain_report, outcome_counts, output_table, pair_saved_outputs, report_key
from .storage import read_json, rows
from .tables import markdown
from .trajectory import late_rewards, quarter_table, training_quarters


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


def different_group_credit(first, second):
    """Two constant binary vectors both produce zero GRPO advantages even when their rewards differ."""
    return first != second and (len(set(first)) > 1 or len(set(second)) > 1)


def compare_training_groups(shallow, deep):
    """Find real optimizer groups that received identical solver texts and identical lower reviews in both runs."""
    matched, different = [], []
    for update, (left, right) in enumerate(zip(batched(shallow, 4), batched(deep, 4), strict=True), 1):
        if not all(a["key"] == b["key"] and a["answer"] == b["answer"] and a["reports"] == b["reports"][:2]
                   for a, b in zip(left, right, strict=True)):
            continue
        matched.append(update)
        if different_group_credit([row["reward"] for row in left], [row["reward"] for row in right]):
            different.append(update)
    return dict(matched=matched, different_credits=different)


def group_evidence(deep):
    """Replay both reward rules on identical samples, preserving the four-way GRPO groups."""
    fixes = harms = changed = 0
    preferences = [Counter(), Counter()]
    paid = [dict(correct=0,wrong=0) for _ in range(2)]
    credit_example = None
    pattern_groups = groups_without_harm = 0
    flips = [dict(reject_to_accept=0, accept_to_reject=0) for _ in range(2)]
    for group in batched(deep, 4):
        if len(group) != 4:
            raise ValueError("A comparison requires four samples per group")
        labels = [r["label"] for r in group]
        second, third = [[effective_bit(r["reports"][index]) for r in group] for index in (1, 2)]
        directions = [(y, b) for a, b, y in zip(second, third, labels, strict=True) if a != b]
        for label, accepted in directions:
            flips[int(label)]["reject_to_accept" if accepted else "accept_to_reject"] += 1
        pattern = second == labels and (1, 0) in directions and (0, 1) in directions
        pattern_groups += pattern
        if credit_example is None and pattern:
            credit_example = dict(update=group[0]["step"]+1, expression=group[0]["expression"],
                                  reports=[row["reports"][1:3] for row in group],
                                  samples=[[row["answer"], bool(row["label"]), a, b]
                                           for row, a, b in zip(group, second, third, strict=True)])
        for counts, votes in zip(paid,(second,third),strict=True):
            for label,bit in zip(labels,votes,strict=True):
                counts["correct" if label else "wrong"] += bit
        group_harms = sum(accepted != truth for truth, accepted in directions)
        harms += group_harms
        fixes += len(directions) - group_harms
        groups_without_harm += group_harms == 0
        changed += different_group_credit(second, third)
        for i, j in combinations(range(4), 2):
            if labels[i] == labels[j]:
                continue
            good, bad = (i, j) if labels[i] else (j, i)
            for counts, votes in zip(preferences, (second, third), strict=True):
                counts[votes[good] - votes[bad]] += 1
    return dict(fixes=fixes, harms=harms, changed_groups=changed, same_answers_paid=paid, credit_example=credit_example,
                verdict_flips=flips, example_pattern_groups=pattern_groups, groups_without_new_errors=groups_without_harm,
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
    return training, dev, dict(training=parts, rewarded=paid, dev=cases, first_quarter=windows[0],
                               last_quarter=windows[1], quarters=training_quarters(training))


def fixed_answer_replay(records):
    """Reconstruct both graders' decisions while holding one checkpoint's written solutions fixed."""
    accepted, agreement = [0, 0], [0, 0]
    transitions = []
    for row in records:
        reports = row["reports"][1:3]
        verdicts = [effective_bit(report) for report in reports]
        if len(verdicts) != 2 or verdicts != row["verdicts"][1:3]:
            raise ValueError("The fixed-answer replay disagrees with the logged verdicts")
        for i, bit in enumerate(verdicts):
            accepted[i] += bit
            agreement[i] += bit == row["correct"]
        if verdicts[0] != verdicts[1]:
            transitions.append(dict(expression=row["expression"], output=row["trace"], truth=row["expected_values"],
                                    bits=verdicts, reports=reports, correct=row["correct"]))
    fixes = sum(change["bits"][1] == change["correct"] for change in transitions)
    return dict(correct=sum(row["correct"] for row in records), n=len(records), accepted=accepted,
                identical_reports=sum(row["reports"][1] == row["reports"][2] for row in records),
                agreement=agreement, fixes=fixes, harms=len(transitions)-fixes, transitions=transitions)


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
    paired = Counter()
    shared_error = None
    for a, b in zip(dev2, dev3, strict=True):
        outcome = "both" if a["correct"] and b["correct"] else "two only" if a["correct"] else "three only" if b["correct"] else "neither"
        paired[outcome] += 1
        if shared_error is None and a["correct"] and not b["correct"] and not b["malformed"] and b["verdicts"] == [1,1,1]:
            shared_error = dict(expression=b["expression"], right=a["trace"], wrong=b["trace"])
    replays = [fixed_answer_replay(dev2), fixed_answer_replay(dev3)]
    # Published study.json revisions exposed these three-judge replay fields at the top level.
    original_replay = {key: replays[1][key] for key in ("accepted", "agreement", "transitions")}
    return dict(seed=seed, n=len(deep), groups=len(deep)//4, dev_n=len(dev3), two=stats2, three=stats3,
                paired_outputs=pair_saved_outputs(dev2, dev3), matched_training=compare_training_groups(shallow, deep),
                paired=paired, replays=replays, shared_error=shared_error, **original_replay,
                transcript_audit=read_json(directory/"diagnostics"/f"depth-transcripts-{seed}.json"), **group_evidence(deep))


def reward_rates(r):
    """Compare final-bit reward rates on the identical examples at each depth."""
    valid = r["three"]["training"]["correct"]
    wrong = r["n"]-valid
    records = []
    for level,paid in enumerate(r["same_answers_paid"],2):
        counts = [(paid["correct"],valid),(paid["wrong"],wrong)]
        cells = [f"{n}/{total} ({100*n/total:.1f}%)" if total else "0/0" for n,total in counts]
        gap = f"{100*(paid['correct']/valid - paid['wrong']/wrong):+.1f}" if valid and wrong else "—"
        records.append([f"Judge {level}",*cells,gap])
    return markdown(["Frozen reward source","Correct answers rewarded","Wrong answers rewarded","Correct minus wrong rate (pp)"],records)


def replay_table(reviews):
    """Reading down the exact-score column compares training. Reading across a row compares graders."""
    rows = []
    for depth, replay in enumerate(reviews, 2):
        counts = [replay["correct"], *replay["accepted"]]
        rows.append([f"Judge {depth}", *(f"{value}/{replay['n']}" for value in counts),
                     replay["fixes"], replay["harms"]])
    return markdown(["Final judge used for training", "Solutions exactly correct", "Judge 2 approved",
                     "Judge 3 approved", "Grading errors Judge 3 fixed", "Grading errors Judge 3 introduced"], rows)


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
        f"Only the solver adapter learned. All judging used the frozen, original Qwen instruction model. "
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
    second, third = r["replays"]
    sections += ["### What changes if we remove Judge 3 during training or during grading?",
        f"**During training**, the final judge rewards the solver after each group of answers. Two copies of the "
        f"starting solver learned separately. They then answered the same {n} development questions and earned "
        f"different arithmetic scores. **During grading**, we took each copy’s saved answers and read Judge 2’s "
        f"and Judge 3’s decisions on exactly that text. Each row below holds the written answers fixed.",
        replay_table(r["replays"]),
        f"The solver trained with Judge 3 earns **{correct}/{n}** from the integer checker whichever grader reads it. "
        f"Judge 3 changed {len(third['transitions'])} decisions on that solver’s answers. It fixed {third['fixes']} "
        f"and introduced {third['harms']}. The **{abs(correct-two_correct)}-solution gap** comes from comparing "
        f"the answers the two solvers wrote after separate training runs.",
        f"On the Judge 2-trained solver’s answers, Judges 2 and 3 agreed with the checker on "
        f"{second['agreement'][0]}/{n} and {second['agreement'][1]}/{n}, respectively. On the Judge 3-trained "
        f"solver’s answers those figures were {third['agreement'][0]}/{n} and {third['agreement'][1]}/{n}. Their "
        f"entire six-number reports were identical on {third['identical_reports']}/{n} of the latter answers. "
        f"The accept/reject decision matched on {n-len(third['transitions'])}/{n}. "
        f"[Two-judge answers](results/calibrated/d2-{seed}/replay.jsonl) · "
        f"[Three-judge answers](results/calibrated/d3-{seed}/replay.jsonl)"]
    if third["transitions"]:
        example_rows = []
        for e in third["transitions"]:
            decisions = []
            for bit, report in zip(e["bits"],e["reports"],strict=True):
                record = numbers(report,6)
                detail = ""
                if record and record[0] not in (0,1):
                    detail = f" (invalid audit flag {record[0]})"
                decisions.append(("Accepted" if bit else "Rejected")+detail)
            example_rows.append([e["expression"],e["output"].replace("\n"," "),",".join(map(str,e["truth"])),*decisions])
        sections += ["Judge 3 changed the following verdicts on the three-judge-trained solver’s saved answers.",
                     markdown(["Problem","Submitted steps","Correct steps","Judge 2","Judge 3"],example_rows)]
    counts = outcome_counts(r["paired_outputs"])
    sections += ["### What did the solvers and judges actually write?",
        f"On {sum(counts.values())} problems only the two-judge-trained solver wrote a correct solution. "
        f"When the graders read the other solver’s wrong answers on those problems, both approved {counts[1,1]}, "
        f"both rejected {counts[0,0]}, Judge 3 caught {counts[1,0]} that Judge 2 approved, and Judge 3 approved "
        f"{counts[0,1]} that Judge 2 rejected. In the reverse direction, only the three-judge-trained solver "
        f"solved {paired['three only']}/{n}.",
        report_key(r["paired_outputs"]),
        "Each pair shows the same question answered by each solver. The judge cells give the decision on the "
        "solver and the literal output, including any incorrect evidence. For Judges 2 and 3, the first three "
        "numbers review the preceding judge. Field four gives the verdict on the solution. Judge 3 also read "
        "the two-judge-trained solver’s answers in this replay.",
        output_table(differing_examples(r["paired_outputs"])),
        f"The examples show the first well-formatted case available for each observed verdict pattern and the "
        f"first reverse outcome. [All {n} paired outputs and judge reports](reports/reviews/paired-outputs-seed-{seed}.md)"]
    sections += ["### What changed during training?",
        f"On the same {r['n']:,} training answers sampled by the three-judge solver, Judge 3 fixed {r['fixes']} "
        f"of Judge 2’s verdicts and spoiled {r['harms']}. Both judges made the same reward decision on "
        f"{r['n']-r['fixes']-r['harms']:,} samples and different decisions on {r['fixes']+r['harms']:,} "
        f"({100*(r['fixes']+r['harms'])/r['n']:.1f}%). A previously correct grade became wrong on "
        f"{100*r['harms']/r['n']:.1f}% of all samples. "
        f"Substituting Judge 2’s reward would have changed the "
        f"relative credits in **{r['changed_groups']}/{r['groups']} optimizer updates**. "
        "Each GRPO update compares four answers to one question. When gradings change early on, the solvers can "
        "learn different answers and receive different training data at subsequent updates. "
        "[GRPO advantage calculation](https://huggingface.co/docs/trl/grpo_trainer#computing-the-advantage)",
        "Reading each frozen verdict on exactly the same sampled answers measures the change in reward for correct "
        "and incorrect arithmetic. A positive rate difference means correct answers receive reward more often.",
        reward_rates(r),
        markdown(["Exact grade of the training answer","Judge 2 rejected → Judge 3 accepted",
                  "Judge 2 accepted → Judge 3 rejected"],
                 [[label,r["verdict_flips"][idx]["reject_to_accept"],r["verdict_flips"][idx]["accept_to_reject"]]
                  for label,idx in (("Correct",1),("Wrong",0))]),
        f"During its own training run, the two-judge solver generated {r['two']['training']['correct']}/{r['n']:,} "
        f"exact answers and received {sum(r['two']['rewarded'].values())} positive rewards. The three-judge solver "
        f"generated {deep['training']['correct']}/{r['n']:,} exact answers and received {sum(deep['rewarded'].values())} positive rewards. "
        "Each run sampled from its own evolving solver.",
        markdown(["Within the same training question", "Correct answer ranks higher", "Tied", "Wrong answer ranks higher"],
                 [["Judge 2 on those answers",*r["j2_pairs"]],["Judge 3 on those answers",*r["j3_pairs"]]]),
        "Each column pair below splits the assigned rewards by the independent arithmetic grade. All four "
        "training quarters use the same question schedule across runs, and each solver samples its own answers.",
        quarter_table(r), late_rewards(r),
        "![Fraction of training answers exactly correct and fraction rewarded in each quarter for both solvers](docs/assets/depth-trajectory.png)"]
    matched = r["matched_training"]
    sections.append(f"We also compared the **two actual training runs** while matching the prompt, all four solver "
                    f"texts and all Judge 1 and Judge 2 reports word for word. This held at {len(matched['matched'])}/"
                    f"{r['groups']} updates. The reward used in each run gave the samples different relative credit "
                    f"at {len(matched['different_credits'])} of these matched updates.")
    if example := r["credit_example"]:
        both_runs = example["update"] in matched["matched"]
        source = ("Both runs sampled these same four answers and produced the same lower reports. The last two "
                  "columns show the rewards used in the two training runs." if both_runs else
                  "The two reward columns compare the preceding report with the actual reward on this solver’s samples.")
        correct_samples = [s for s in example["samples"] if s[1]]
        wrong_samples = [s for s in example["samples"] if not s[1]]
        def rewarded(samples, column):
            return f"{sum(s[column] for s in samples)}/{len(samples)}"
        sections += [
            f"At optimizer update {example['update']}, the three-judge run sampled four answers to "
            f"`{example['expression']}`. The table shows the first group in which Judge 2 graded every sample correctly "
            "and Judge 3 both removed a correct answer’s reward and awarded a wrong answer. Each duplicate "
            f"was a separate sampled completion with its own sampled judge reports. {source}",
            markdown(["Solver wrote", "Exact checker", "Judge 2 reward used for training" if both_runs else "Judge 2 reward on this sample",
                      "Judge 3 reward used for training"],
                     [[answer, "correct" if label else "wrong", f"**{a}** · {explain_report(j2,2,a)}",
                       f"**{b}** · {explain_report(j3,3,b)}"]
                      for (answer,label,a,b),(j2,j3) in zip(example["samples"],example["reports"],strict=True)]),
            f"Judge 2 rewarded **{rewarded(correct_samples,2)} correct attempts** and "
            f"**{rewarded(wrong_samples,2)} wrong attempts**. Judge 3 rewarded "
            f"**{rewarded(correct_samples,3)} correct attempts** and **{rewarded(wrong_samples,3)} wrong attempts**. "
            f"Each individual attempt received either one point or zero. Across the run, "
            f"**{r['example_pattern_groups']}/{r['groups']} groups** met the selection rule for this example. "
            f"In **{r['groups_without_new_errors']}/{r['groups']} groups**, Judge 3 introduced zero new grading errors.",
            f"[Two-judge training records](results/calibrated/d2-{seed}/rollouts.jsonl) · "
            f"[Three-judge training records](results/calibrated/d3-{seed}/rollouts.jsonl)"]
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
        _, third = r["replays"]
        sections.extend([f"## Seed {seed}",
            f"On {r['dev_n']} matched development problems the two-judge solver alone was correct on "
            f"{r['paired']['two only']}, the three-judge solver alone on {r['paired']['three only']}, both on "
            f"{r['paired']['both']}, and neither on {r['paired']['neither']}. Each row below uses a different trained "
            f"solver on those same questions. The two graders read identical saved text within each row.",
            replay_table(r["replays"]),
            f"[Every paired solver output and all three raw judge reports](paired-outputs-seed-{seed}.md)",
            markdown(["Three-judge solver error", "Development answers", "Training answers", "Training answers rewarded"],
                     [[k,deep["dev"][k],deep["training"][k],deep["rewarded"][k]] for k in
                      ("correct","first wrong, second consistent","first wrong, second inconsistent","second wrong","format")]),
            f"On the same {r['n']} training answers, Judge 3 fixed {r['fixes']} effective Judge 2 verdicts and "
            f"spoiled {r['harms']}. Its decision changed the within-group advantages in {r['changed_groups']}/{r['groups']} "
            f"optimizer updates. In {r['groups_without_new_errors']}/{r['groups']} groups it introduced zero new errors. "
            f"On {r['example_pattern_groups']}/{r['groups']} groups, Judge 2 got every verdict right and Judge 3 "
            "both removed credit from a correct answer and paid an incorrect answer. Reward rates below compare all "
            "answers of each class on this fixed trajectory.",
            reward_rates(r),
            "Within-question pairs compare correct and incorrect completions of the same problem. "
            "Pairs within and across rows share observations.",
            markdown(["Reward applied to these answers", "Correct ranks higher", "Tied", "Incorrect ranks higher"],
                     [["Judge 2",*r["j2_pairs"]],["Judge 3",*r["j3_pairs"]]]),
            quarter_table(r), late_rewards(r)])
        if third["transitions"]:
            sections.extend(["Every development verdict change on the three-judge solver’s fixed responses is shown below.",
                markdown(["Expression", "Solver", "Exact values", "Judge 2 report", "Judge 3 report", "Verdict change"],
                         [[e["expression"],e["output"].replace("\n"," "),",".join(map(str,e["truth"])), *e["reports"],
                           "Fixed" if e["bits"][1] == e["correct"] else "Introduced error"] for e in third["transitions"]])])
        sections.append(f"[Two-judge records](../../results/calibrated/d2-{seed}) · [Three-judge records](../../results/calibrated/d3-{seed})")
    sections.append("These comparisons distinguish a change of verdict on an already written answer from a change "
                    "to the solver learned over successive updates. Replacing the reward in an archived group reveals "
                    "which relative credits would change on those samples. A separately trained solver generates its "
                    "own subsequent samples. The checker-gated and shuffled arms test sensitivity to reward quality. "
                    "The registered effectiveness claim uses unseen problems and multiple training seeds. "
                    "[Protocol](../preregistration.md) · [All training arms](../summary.md)")
    return "\n\n".join(sections)+"\n"
