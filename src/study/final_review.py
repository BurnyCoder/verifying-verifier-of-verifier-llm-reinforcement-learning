"""Reproduce the final scores and validate the realized cohorts once the campaign is complete."""

from datetime import datetime
from math import isclose

from .benchmark import population
from .curriculum import EXAMPLES
from .depth_review import numbers
from .design import SEEDS, matrix
from .domain import Problem, problems
from .exposures import check_exposures
from .learning_review import execute_steps
from .records import expected, mask_evidence, terminal
from .storage import read_json, rows
from .tables import markdown


def cohort_rows(path, pool, split):
    """Every observation must match one registered expression and a unique canonical ID."""
    seen = set()
    for row in rows(path):
        key = row["key"]
        if key in seen:
            raise ValueError(f"Duplicate problem in {path} at {key}")
        p = pool.get(key)
        if p is None or row["expression"] != p.expression or row["split"] != split:
            raise ValueError(f"Unexpected problem assignment in {path} at {key}")
        seen.add(key)
        yield p, row
    if seen != pool.keys():
        raise ValueError(f"Incomplete cohort in {path}")


def grade_solutions(path, pool, split, fixed_traces=None):
    """Execute the recorded steps and separately check the submitted trace, last value and format."""
    outcomes = {}
    for p,r in cohort_rows(path,pool,split):
        truth = execute_steps(p)
        answer = numbers(r["trace"],len(truth))
        flags = (answer == truth, answer is not None and answer[-1] == truth[-1], answer is None)
        if (tuple(r["problem"]) != p.steps or tuple(r["expected_values"]) != truth or
                (r["correct"],r["final_correct"],r["malformed"]) != flags):
            raise ValueError(f"Arithmetic grade mismatch in {path} at {p.key}")
        outcomes[p.key] = int(answer == truth)
        if fixed_traces is not None:
            reports = r["reports"]
            bits = [terminal(report,i) for i,report in enumerate(reports,1)]
            sound = [numbers(raw,3 if i==0 else 6) == expected(p,r["trace"],reports[:i]) for i,raw in enumerate(reports)]
            flat = sum(terminal(v,1) for v in r["votes"]) >= 2
            correct = outcomes[p.key]
            if (r["trace"] != fixed_traces[p.key] or len(bits) != 3 or len(r["votes"]) != 3 or
                    bits != r["verdicts"] or sound != r["full_report_correct"] or flat != r["flat"] or
                    (r["fixed"],r["harmed"]) != (bits[1]!=correct and bits[2]==correct, bits[1]==correct and bits[2]!=correct)):
                raise ValueError(f"Natural review mismatch in {path} at {p.key}")
    return outcomes


def grade_twins(path, pool, split, novel):
    """Verify the evidence-only intervention and demand the complete expected report on both twins."""
    count = 0
    for p,r in cohort_rows(path,pool,split):
        reviews = r["reviews"]
        labels = [expected(p,r["trace"],[r["first"],report]) for report in reviews]
        if (len(labels) != 2 or {label[0] for label in labels} != {0,1} or
                labels != list(map(tuple,r["labels"])) or mask_evidence(reviews[0]) != mask_evidence(reviews[1])):
            raise ValueError(f"Twin labels or masked evidence differ in {path} at {p.key}")
        good,bad = (numbers(report,6) for report in reviews)
        if labels[0][0] == 0:
            good,bad = bad,good
        if good is None or bad is None or good[:2]+good[3:] != bad[:2]+bad[3:]:
            raise ValueError(f"Twin intervention changed a verdict or another field in {path}")
        correct_mutation = (bad[2] == (abs(good[2])+3 if good[2] < 0 else -(abs(good[2])+3))
                            if novel else abs(bad[2]-good[2]) == 1)
        if not correct_mutation:
            raise ValueError(f"Wrong numerical intervention in {path} at {p.key}")
        for condition in ("visible","masked"):
            matches = [numbers(answer,6) == label for answer,label in zip(r[condition],labels,strict=True)]
            if r[condition+"_pair"] != all(matches):
                raise ValueError(f"Twin pair grade mismatch in {path} at {p.key}")
        count += 1
    return count


def review_completed(original, data):
    """Run only after every final stage, so the review cannot influence model or cohort selection."""
    if not data.get("completed"):
        return None
    profile = data["profile"]
    root = original/("calibrated" if profile else "")
    schedule = matrix(profile)
    seal = read_json(root/"seal.json")
    if (set(seal["weights"]) != {r.name for r in schedule} or
            seal["ordered_training_exposures"] != check_exposures(root,schedule)):
        raise ValueError("The training exposures or checkpoint manifest differ from the published seal")
    suites = dict(test=2048,layout=128,long=128,mechanism=128)
    if profile and profile["family"] != "registered":
        suites["original-difficulty"] = 2048
    pools = {split:{p.key:p for p in (population(profile,split,n) or problems(split,n))} for split,n in suites.items()}
    all_test = set().union(*(pool.keys() for pool in pools.values()))
    if any(len(pools[s])!=n for s,n in suites.items()) or len(all_test) != sum(suites.values()):
        raise ValueError("Distinct final cohorts share a canonical expression or have a missing ID")
    old = {Problem.from_expression(e).key for e in EXAMPLES}
    for location in {original, root}:
        for pattern in ("*/rollouts.jsonl","*/replay.jsonl","corpora/*.jsonl","learnability/**/*.jsonl"):
            for path in location.glob(pattern):
                old.update(r["key"] for r in rows(path))
    leakage = len(all_test & old)
    if leakage:
        raise ValueError(f"Found {leakage} final IDs among previously observed study examples")

    sealed_at = datetime.fromisoformat(seal["time"])
    outcomes, origins = {}, {}
    graded = natural = twins = 0
    unique_twins = {}
    names = {"base":"solver",**{r.name:r.role for r in schedule}}
    prefix = dict(list(pools["test"].items())[:128])
    for name,role in names.items():
        directory = root/name
        dev, final = [read_json(directory/(phase+".json")) for phase in ("development","final")]
        weights = seal["weights"].get(name,"frozen base")
        if (dev["weights"] != weights or final["weights"] != weights or
                not datetime.fromisoformat(dev["time"]) <= sealed_at <= datetime.fromisoformat(final["time"])):
            raise ValueError(f"Evaluation receipt does not match the checkpoint seal for {name}")
        if role == "solver":
            for split,pool in pools.items():
                if split == "mechanism":
                    continue
                labels = grade_solutions(directory/(split+".jsonl"),pool,split)
                graded += len(labels)
                if split=="test":
                    outcomes[name] = labels
        if name in ("base","d3-17") or role.startswith("j"):
            origin = name if name=="d3-17" else "base"
            if origin not in origins:
                origins[origin] = {r["key"]:r["trace"] for r in rows(root/origin/"test.jsonl") if r["key"] in prefix}
            natural += len(grade_solutions(directory/"judge-test.jsonl",prefix,"test",origins[origin]))
        if name=="base" or role=="j3" or name in ("exact-prefix3","top-prefix3","alt-exact-solver","alt-top-solver"):
            for filename,split,novel in (("mechanism","mechanism",False),("unseen-evidence","mechanism",True),
                                         ("layout-evidence","layout",False),("transfer-evidence","layout",True)):
                path = directory/(filename+".jsonl")
                source = final["evidence_sources"][path.name]
                if source != name and list(rows(path)) != list(rows(root/source/path.name)):
                    raise ValueError(f"Reused reviewer measurements differ in {path}")
                count = grade_twins(path,pools[split],split,novel)
                twins += count
                unique_twins[source,filename] = count

    comparisons = []
    for reference in ("d2","flat","d1"):
        seeds = SEEDS[:1] if reference=="d1" else SEEDS
        for seed in seeds:
            a,b = (outcomes[f"{arm}-{seed}"] for arm in ("d3",reference))
            gains = sum(a[k]>b[k] for k in a)
            losses = sum(a[k]<b[k] for k in a)
            change = (gains-losses)/len(a)
            if reference!="d1":
                published = data["primary" if reference=="d2" else "flat"]["per_seed"][str(seed)]
                if not isclose(change,published,abs_tol=1e-12):
                    raise ValueError("Paired published effect differs from independently rescored solutions")
            comparisons.append([seed,reference.upper(),len(a),gains,losses,f"{100*change:+.2f}"])
    return dict(checkpoints=len(schedule),prior_ids=len(old),test_ids=len(all_test),overlap=leakage,solver_grades=graded,
                natural_reviews=natural,paired_records=twins,distinct_paired_records=sum(unique_twins.values()),
                comparisons=comparisons)


def review_text(audit):
    return (f"# Final scientific review\n\nAll {audit['checkpoints']} trained checkpoint identities matched the "
            f"development, seal and final receipts. The actual optimizer exposures reproduced the sealed order digests. "
            f"Across {audit['test_ids']} distinct reserved IDs and {audit['prior_ids']} earlier canonical IDs, the "
            f"observed overlap was {audit['overlap']}. Each method used its entire registered cohort.\n\n"
            f"Executing the numbered programs reproduced all {audit['solver_grades']} solver grades over the primary "
            f"and transfer populations. A separate replay checked {audit['natural_reviews']} natural reviews against "
            f"the saved solver answers, including the direction of each changed verdict. We rechecked "
            f"{audit['paired_records']} stored evidence-pair records, representing {audit['distinct_paired_records']} "
            "reviewer–intervention measurements after recognizing reused outputs.\n\n"
            +markdown(["Seed","Compare D3 to","Paired problems","Only D3 correct","Only comparator correct","D3 minus comparator (pp)"],
                      audit["comparisons"])+"\n\nThe D1 contrast is descriptive and uses a single training seed. The "
            "primary D3–D2 inference resamples problem IDs jointly across all registered checkpoints. The selected "
            "arithmetic population, shared model backbone and finite seed set limit generalization. "
            "[Paired intervals](../summary.md) · [Preregistration](../preregistration.md) · "
            "[Review code](../../src/study/final_review.py)\n")
