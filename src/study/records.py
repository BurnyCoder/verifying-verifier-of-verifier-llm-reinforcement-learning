"""Executable semantics for solution reports and reviews of previous reports."""

import re

_RECORD = re.compile(r"[+-]?[0-9]{1,14}(?:\s*,\s*[+-]?[0-9]{1,14})*")


def parse(text, width):
    """Accept an entire bounded integer record, with optional matching square brackets."""
    text = text.strip()
    if text.startswith("[") and text.endswith("]"):
        text = text[1:-1].strip()
    if len(text) > 1024 or not _RECORD.fullmatch(text):
        return None
    values = tuple(map(int, text.split(",")))
    return values if len(values) == width else None


def render(record):
    return ",".join(map(str, record))


def named_values(text, width):
    """Secondary analysis of one explicit sN = integer assignment per line, in listed order."""
    lines=text.strip().splitlines()
    if len(lines)!=width:
        return None
    result=[]
    for index,line in enumerate(lines,1):
        match=re.fullmatch(rf"\s*s{index}\s*=\s*([+-]?[0-9]{{1,14}})\s*",line)
        if not match:
            return None
        result.append(int(match[1]))
    return tuple(result)


def solver_truth(problem, trace):
    """Provide an exact first-fault witness, including independently correct final answers."""
    predicted = parse(trace, len(problem.values))
    if predicted is None:
        return (0, -1, 0)
    for step, (value, truth) in enumerate(zip(predicted, problem.values, strict=True), 1):
        if value != truth:
            return (0, step, truth)
    return (1, 0, problem.values[-1])


def audit(previous, ideal, solution):
    """A positive meta-verdict certifies the predecessor, irrespective of solver acceptance."""
    observed = parse(previous, len(ideal))
    if observed is None:
        return (0, -1, 0, *solution)
    for field, (seen, wanted) in enumerate(zip(observed, ideal, strict=True), 1):
        if seen != wanted:
            return (0, field, wanted, *solution)
    return (1, 0, ideal[-1], *solution)


def expected(problem, trace, history):
    solution = solver_truth(problem, trace)
    ideal = solution
    for report in history:
        ideal = audit(report, ideal, solution)
    return ideal


def terminal(text, depth):
    """Learned rewards consult the solution bit in the last report, never the oracle."""
    record = parse(text, 3 if depth == 1 else 6)
    return int(record is not None and record[-3] == 1 and (depth == 1 or record[0] in (0, 1)))


def approval(text):
    """A top-down judge trains the immediately subordinate judge on its soundness bit."""
    record = parse(text, 6)
    return int(record is not None and record[0] == 1 and record[-3] in (0, 1))


def sound(text, truth):
    return parse(text, len(truth)) == truth


def mask_evidence(text):
    """The two masked twins are identical, including their visible solution and audit bits."""
    record = parse(text, 6)
    return "malformed" if record is None else f"{record[0]},?, ?,{record[3]},?,?"
