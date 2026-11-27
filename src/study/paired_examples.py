"""Publish the two solvers' literal development outputs alongside their frozen-judge replays."""

from collections import Counter
from html import escape

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


def output_table(pairs):
    """Decode effective solution verdicts separately from each judge's verbatim report."""
    records = []
    for pair in pairs:
        truth = ",".join(map(str, pair["truth"]))
        for depth, output in enumerate(pair["outputs"], 2):
            problem = f"{literal(pair['expression'])} → {literal(truth)}" if depth == 2 else "↳ same problem"
            exact = "correct" if output["correct"] else "wrong"
            reports = [f"{'accept' if bit else 'reject'} {literal(report)}"
                       for bit, report in zip(output["verdicts"], output["reports"], strict=True)]
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
        "Each judge column gives its effective verdict on the solution followed by the literal model output.",
        "Judge 1 returns the solution verdict, first faulty step and correction. A sound solution uses step zero "
        "and the final answer. Judges 2 and 3 first return whether the preceding report was sound, the first "
        "faulty field and its replacement. Their last three fields grade the solver. Invalid required verdict "
        "flags or unparseable reports yield an effective rejection. The independent integer checker determines "
        "the correct or wrong label in the solver column.",
        output_table(review["paired_outputs"]),
        f"[Two-judge replay](../../results/calibrated/d2-{seed}/replay.jsonl) · "
        f"[Three-judge replay](../../results/calibrated/d3-{seed}/replay.jsonl) · [Depth analysis](depth-diagnosis.md)",
    ]) + "\n"
