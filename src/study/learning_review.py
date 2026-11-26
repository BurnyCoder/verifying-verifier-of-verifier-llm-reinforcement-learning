"""Verify the positive control against its published prompts, checkpoints' outputs and split IDs."""

import operator

from .curriculum import curriculum_problems
from .design import PILOTS, Run
from .domain import Problem
from .exposures import check_exposures
from .learnability_analysis import learning_result
from .records import parse
from .storage import read_json, rows


def execute_steps(problem):
    """Interpret the numbered operations directly, independently of the generator's numeric values."""
    variables = {}
    operations = {"+":operator.add, "-":operator.sub, "*":operator.mul}
    for line in problem.steps:
        target, _, left, sign, right = line.split()
        operands = [variables[t] if t.startswith("s") else int(t) for t in (left,right)]
        variables[target] = operations[sign](*operands)
    return tuple(variables.values())


def check_release(results):
    calibration = results/"learnability"
    published = read_json(calibration/"learning.json")
    if not published:
        return None
    c = read_json(calibration/"screen.json")["selected"]
    family, style = c["family"], c["style"]
    controls = [Run(name, family=family, prompt_style=style) for name in PILOTS]
    exposure = check_exposures(results, controls)
    for spec in controls:
        trained = read_json(results/spec.name/"trained.json")
        settings = trained["run"]
        if (trained["updates"],settings["seed"],settings["family"],settings["prompt_style"]) != (128,17,family,style):
            raise ValueError(f"Unmatched training configuration in {spec.name}")

    # Check realized exposures against the registered assignment, then check them against one another.
    seen = {r["key"] for r in rows(results/PILOTS[0]/"rollouts.jsonl")}
    def expected_ids(phase,n):
        return {p.key for p in curriculum_problems(family,phase,n)}
    if seen != expected_ids("train",128):
        raise ValueError("Unexpected learning-control training problems")
    validation = expected_ids("validation",256)
    partitions = [seen,validation]
    for phase,n in (("screen",16),("confirm",48)):
        ids = [r["key"] for r in rows(calibration/phase/(family+"-"+style+".jsonl"))]
        if len(ids)!=n or set(ids)!=expected_ids(phase,n):
            raise ValueError(f"Unexpected {phase} problems")
        partitions.append(set(ids))
    overlap = sum(map(len,partitions))-len(set.union(*partitions))
    if overlap:
        raise ValueError("The realized calibration partitions overlap")

    samples = []
    for name in ("base",*PILOTS):
        labels = {}
        parsed = 0
        for r in rows(calibration/"evaluations"/(name+".jsonl")):
            p = Problem.from_expression(r["expression"])
            values = execute_steps(p)
            answer = parse(r["trace"],len(values))
            if (r["key"]!=p.key or p.key in labels or tuple(r["expected_values"])!=values or
                r["parsed"]!=(answer is not None) or r["correct"]!=(answer==values)):
                raise ValueError(f"Invalid problem or grade in {name}")
            labels[p.key] = int(answer==values)
            parsed += answer is not None
        marker = read_json(calibration/"evaluations"/(name+".json"))
        if labels.keys()!=validation or (marker["n"],marker["correct"],marker["parsed"])!=(len(labels),sum(labels.values()),parsed):
            raise ValueError(f"Validation cohort or summary mismatch for {name}")
        samples.append(labels)
    recalculated = learning_result(*samples)
    if any(published.get(field)!=value for field,value in recalculated.items()):
        raise ValueError("The published paired result differs from the raw validation outcomes")
    return dict(training=len(seen),validation=len(validation),scored=sum(map(len,samples)),overlap=overlap,
                exposure_hash=exposure[PILOTS[0]],fixed=published["over_base"]["fixed"],harmed=published["over_base"]["harmed"])


def review_text(check):
    return (f"# Scientific review of the learnability control\n\n"
            f"The exact and shuffled policies saw the same {check['training']} unique training problems in the same "
            f"optimizer-update order, in four-completion groups. Their ordered exposure SHA-256 is `{check['exposure_hash']}`. "
            f"Across observed training, difficulty screening, confirmation and learning validation there were "
            f"{check['overlap']} repeated canonical IDs between partitions.\n\n"
            f"All {check['scored']} responses from the three checkpoints were rescored on the same {check['validation']} "
            f"validation problems by executing the numbered operations. Every grade, parse flag, checkpoint summary, "
            f"paired estimate and interval agreed with the published observations. Exact-reward training fixed "
            f"{check['fixed']} previously incorrect traces and lost {check['harmed']} correct traces.\n\n"
            "The population was selected on development data. The learning interval conditions on one training seed "
            "and these checkpoints. It addresses whether this solver learns arithmetic with an informative reward. "
            "The separate depth comparison uses fresh solvers, multiple seeds and a sealed evaluation. "
            "[Registered decision rule](../learnability-preregistration.md) · [Outcomes and examples](../learnability.md) "
            "· [Validation records](../../results/learnability/evaluations) · [Verification code](../../src/study/learning_review.py)\n")
