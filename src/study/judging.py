"""Batched independent judge calls, depth routing, and train-only judge examples."""

import random

from .records import expected, render, solver_truth, terminal


def chain(backend, problems, traces, snapshots, depth, seed, sample=True):
    """History for each answer is private to that answer and grows by one report per depth."""
    histories = [[] for _ in traces]
    for level in range(1, depth+1):
        role = f"j{level}"
        prompts = [backend.prompt(role, p, t, h) for p, t, h in zip(problems, traces, histories, strict=True)]
        answers = backend.generate(prompts, snapshots[level-1], role, seed + level, sample)
        for history, answer in zip(histories, answers, strict=True):
            history.append(answer)
    return histories


def votes(backend, problems, traces, seed, snapshots=(None, None, None)):
    prompts = [backend.prompt("j1", p, t) for p, t in zip(problems, traces, strict=True)]
    samples = [backend.generate(prompts, snapshots[0], "flat_j1", seed+101+i, True) for i in range(3)]
    return [list(items) for items in zip(*samples, strict=True)]


def majority(reports):
    return int(sum(terminal(r, 1) for r in reports) >= 2)


def make_example(problem, role, index, natural):
    """Balance natural examples with valid, evidence-wrong and verdict-wrong predecessors."""
    level = int(role[1:])
    if index % 4 == 0:
        return natural["trace"], natural["reports"][:level-1]
    rng = random.Random(int(problem.key[:12], 16) + index)
    values = list(problem.values)
    if rng.randrange(2):
        position = rng.randrange(len(values))
        values[position] += rng.choice((-2, -1, 1, 2))
    trace, history = render(values), []
    for _ in range(level-1):
        record = list(expected(problem, trace, history))
        choice = rng.randrange(4)
        if choice == 1:
            record[0] = 1-record[0]
        elif choice == 2:
            record[-1] += 1
        elif choice == 3 and len(record) == 6:
            record[2] += 1
        history.append(render(record))
    return trace, history


def twin(problem, index, transfer=False):
    values = list(problem.values)
    if index % 2:
        values[index % len(values)] += 1
    trace = render(values)
    j1 = list(solver_truth(problem, trace))
    if index % 4 >= 2:
        j1[-1] += 1
    first = render(j1)
    good = list(expected(problem, trace, [first]))
    bad = good.copy()
    bad[2] = (-bad[2] if bad[2] else -2) if transfer else bad[2] + (1 if index % 2 else -1)
    return trace, first, render(good), render(bad)
