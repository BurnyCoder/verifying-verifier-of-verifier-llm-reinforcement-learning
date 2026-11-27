"""Pair fixed solver outputs across reward depths and check what a further review changed."""

from itertools import batched

from .depth_review import different_group_credit, effective_bit, numbers
from .domain import Problem
from .learning_review import execute_steps


def solver_bit(text, depth):
    """Reconstruct the published solution verdict independently of the trainer's reward callback."""
    if depth == 1:
        record = numbers(text, 3)
        return int(record is not None and record[0] == 1)
    return effective_bit(text)


def audit_intervention(rollouts, lower, upper):
    """Hold each solver group fixed and substitute its own lower judge's recorded decisions."""
    fixed = harmed = changed = groups = 0
    for group in batched(rollouts,4):
        if len(group) != 4:
            raise ValueError("A reward intervention requires a complete optimizer group")
        before, after = [[solver_bit(r["reports"][d-1],d) for r in group] for d in (lower,upper)]
        for a,b,r in zip(before,after,group,strict=True):
            fixed += a != b and b == r["label"]
            harmed += a != b and b != r["label"]
        changed += different_group_credit(before,after)
        groups += 1
    return dict(samples=4*groups,groups=groups,fixed=fixed,harmed=harmed,changed_credit_groups=changed)


def paired_examples(cohorts):
    """Show the first problem in each observed correctness pattern, preserving every raw audit."""
    seen = set()
    examples = []
    for group in zip(*cohorts,strict=True):
        first = group[0]
        if any(r["key"]!=first["key"] for r in group):
            raise ValueError("Cannot compare example traces on different development problems")
        pattern = tuple(r["valid"] for r in group)
        if pattern in seen:
            continue
        seen.add(pattern)
        p = Problem.from_expression(first["expression"])
        examples.append(dict(key=p.key,expression=p.expression,expected=list(execute_steps(p)),correct=list(pattern),
                             traces=[r["trace"] for r in group],reports=[r["reports"] for r in group]))
    return examples
