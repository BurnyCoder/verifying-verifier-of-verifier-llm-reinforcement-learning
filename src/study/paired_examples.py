"""Publish the two solvers' literal development outputs alongside their frozen-judge replays."""

from collections import Counter
from html import escape

from .domain import Problem
from .records import parse, render, solver_truth, terminal
from .tables import markdown


def pair_saved_outputs(shallow, deep):
    """Keep both independently written answers attached to the same problem and exact steps."""
    pairs = []
    for left, right in zip(shallow, deep, strict=True):
        if any(left[k] != right[k] for k in ("key", "expression", "expected_values")):
            raise ValueError("Both checkpoints must answer the same problem in the same position")
        # A six-field reviewer can reject a prior report and still approve the solver.
        outputs = [{key: row[key] for key in ("trace", "correct", "malformed", "reports", "verdicts")}
                   for row in (left, right)]
        pairs.append(dict(expression=left["expression"], truth=left["expected_values"], outputs=outputs))
    return pairs


def outcome_counts(pairs):
    """On problems only the shallow solver solved, tally J2 and J3 decisions on the deep solver's text."""
    counts = Counter()
    for pair in pairs:
        shallow, deep = pair["outputs"]
        if shallow["correct"] and not deep["correct"]:
            counts[tuple(deep["verdicts"][1:3])] += 1
    return counts


def differing_examples(pairs):
    """Take the first well-formatted loss per observed decision pair, then the first reverse outcome."""
    illustrative = {}
    reverse = None
    for pair in pairs:
        shallow, deep = pair["outputs"]
        if shallow["correct"] and not deep["correct"]:
            key = tuple(deep["verdicts"][1:3])
            existing = illustrative.get(key)
            if existing is None or (existing["outputs"][1]["malformed"] and not deep["malformed"]):
                illustrative[key] = pair
        if reverse is None and deep["correct"] and not shallow["correct"]:
            reverse = pair
    return [*illustrative.values(), *([reverse] if reverse else [])]


def literal(value):
    """Preserve generated strings while protecting the Markdown table from pipes, HTML and line breaks."""
    text = escape(value, quote=False).replace("|", "&#124;").replace("\n", "<br>")
    return f"<code>{text}</code>"


def report_key(pairs):
    """Translate a real acceptance and its contrasting first-step correction using the archive and checker."""
    guide = ("Judge 1 writes three numbers. The first is its verdict (1 means accept, 0 means reject). The "
             "second is the first wrong step (0 means none). The third is the final value it certifies on "
             "acceptance or the correct value at the first faulty step on rejection.")
    for pair in pairs:
        solved, missed = pair["outputs"]
        value = pair["truth"][-1]
        if (not solved["correct"] or missed["correct"] or missed["malformed"]
                or parse(solved["reports"][0], 3) != (1, 0, value)):
            continue
        correction = solver_truth(Problem.from_expression(pair["expression"]), missed["trace"])
        claim = parse(missed["reports"][0], 3)
        reported = f"Judge 1 actually wrote {literal(missed['reports'][0])} for that answer."
        if claim and claim[:2] == (1, 0):
            reported = (f"Judge 1 actually wrote {literal(missed['reports'][0])}, meaning “accept, no wrong "
                        f"step, final value is {claim[2]}.”")
            submitted = parse(missed["trace"], len(pair["truth"]))
            if submitted and submitted[-1] != claim[2]:
                reported += f" The solver’s own final value was {submitted[-1]}."
        return (f"{guide} On {literal(pair['expression'])}, {literal(solved['reports'][0])} means "
                f"“accept, no wrong step, final value is {value}.” For {literal(missed['trace'])} on the same "
                f"problem, the checker gives {literal(render(correction))} because step {correction[1]} should be "
                f"{correction[2]}. {reported}")
    return guide


def solution_claim(verdict, step, value):
    """Translate the final triple as a claim by the judge, including malformed or inconsistent fields."""
    if verdict == 1 and step == 0:
        return f"Accepts the solver and gives {value} as its final value."
    if verdict == 0 and step > 0:
        return f"Rejects the solver and says step {step} should be {value}."
    if verdict == 0 and step == -1:
        return f"Reports a malformed solution and gives {value} in the value field."
    return f"Reports solver flag {verdict}, step {step} and value {value}."


def prior_claim(verdict, field, value, prior):
    """Translate which field the current judge claims to have checked in the preceding report."""
    if verdict == 1 and field == 0:
        return f"Endorses Judge {prior} and supports the value {value}."
    if verdict == 0 and field > 0:
        return f"Flags field {field} of Judge {prior} and proposes {value}."
    if verdict == 0 and field == -1:
        return f"Calls Judge {prior}’s report malformed."
    if verdict not in (0, 1):
        return f"Invalid review flag {verdict}."
    return f"Reports review flag {verdict} and field {field} for Judge {prior}."


def explain_report(raw, depth, effective):
    """Check the effective verdict and distinguish reviewing the judge from grading the arithmetic."""
    if terminal(raw, depth) != effective:
        raise ValueError("The explanation disagrees with the logged effective verdict")
    record = parse(raw, 3 if depth == 1 else 6)
    if record is None:
        return f"Unparseable report. The effective verdict is reject.<br>{literal(raw)}"
    parts = []
    if depth > 1:
        parts.append(prior_claim(*record[:3], depth-1))
    solution = solution_claim(*record[-3:])
    if record[-3] not in (0, 1) or (depth > 1 and record[0] not in (0, 1)):
        parts.extend([f"Its solver fields say “{solution}”", "The effective verdict is reject."])
    else:
        parts.append(solution)
    return " ".join(parts) + "<br>" + literal(raw)


def output_table(pairs):
    """Decode effective solution verdicts separately from each judge's verbatim report."""
    records = []
    for pair in pairs:
        truth = ",".join(map(str, pair["truth"]))
        for depth, output in enumerate(pair["outputs"], 2):
            problem = f"{literal(pair['expression'])} → {literal(truth)}" if depth == 2 else "↳ same problem"
            exact = "correct" if output["correct"] else "wrong"
            reports = [explain_report(raw, level, bit) for level, (raw, bit) in
                       enumerate(zip(output["reports"], output["verdicts"], strict=True), 1)]
            records.append([problem, f"Judge {depth}", f"{literal(output['trace'])} · {exact}", *reports])
    return markdown(["Problem → exact steps", "Training reward", "Solver wrote", "Judge 1", "Judge 2", "Judge 3"], records)


def paired_text(review):
    """Give every question a row pair in original order so readers can check the development diagnosis."""
    seed = review["seed"]
    return "\n\n".join([
        f"# Every paired solver output and judge report for seed {seed}",
        f"Two separately trained solvers answered the same {review['dev_n']} development questions. The first "
        "row for each question uses the solver trained with two frozen judges. The next row uses the solver "
        "trained with three. After training, both sets of saved answers went through all three judges. "
        "Each judge column translates its claims into plain language, with the original output underneath.",
        report_key(review["paired_outputs"]),
        "Judges 2 and 3 first return whether the preceding report was sound, the first "
        "faulty field and its replacement. Their last three fields grade the solver. Invalid required verdict "
        "flags or unparseable reports yield an effective rejection. The independent integer checker determines "
        "the correct or wrong label in the solver column.",
        output_table(review["paired_outputs"]),
        f"[Two-judge replay](../../results/calibrated/d2-{seed}/replay.jsonl) · "
        f"[Three-judge replay](../../results/calibrated/d3-{seed}/replay.jsonl) · [Depth analysis](depth-diagnosis.md)",
    ]) + "\n"
