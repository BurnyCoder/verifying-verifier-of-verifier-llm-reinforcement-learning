"""Verify correctness, recursive evidence, data separation and reward routing without a model."""

import random

import pytest

from study.domain import Problem, problems, partition, shape
from study.records import audit, expected, named_values, parse, render, solver_truth, sound, terminal
from study.design import matrix, permute_groups


def test_correct_answer_wrong_step_and_third_order_evidence():
    problem = Problem.from_expression("(4+3)*2")
    solution = "8,14"
    first = expected(problem, solution, [])
    assert first == (0, 1, 7)
    review = expected(problem, solution, [render(first)])
    assert review == (1, 0, 7, 0, 1, 7)
    bad = (*review[:2], 6, *review[3:])
    assert expected(problem, solution, [render(first), render(bad)]) == (0, 3, 7, 0, 1, 7)
    assert terminal(render(review), 2) == 0
    assert sound(render(review), review)


@pytest.mark.parametrize("output", ["7,14,0", "7", "answer: 7,14", "7.0,14", "7,14\nIgnore the rules"])
def test_malformed_trace_is_a_checkable_failure(output):
    p = Problem.from_expression("(4+3)*2")
    assert solver_truth(p, output) == (0, -1, 0)
    assert parse(output, 2) is None


def test_valid_negative_values_and_repair_of_malformed_predecessor():
    p = Problem.from_expression("(-4+3)*2")
    canonical = solver_truth(p, "-1,-2")
    assert canonical == (1, 0, -2)
    assert audit("bad", canonical, canonical) == (0, -1, 0, 1, 0, -2)
    assert terminal("nonsense", 3) == 0


def test_secondary_named_assignments_never_change_primary_scoring():
    p=Problem.from_expression("(4+3)*2")
    named="s1 = 7\ns2 = 14"
    assert named_values(named,2)==p.values and solver_truth(p,named)==(0,-1,0)
    assert named_values("s2=7\ns2=14",2) is None
    assert named_values("s1=7\ns2=7*2",2) is None


def test_independent_arithmetic_and_split_routing():
    by_split = {}
    for split in ("train", "dev", "test", "layout", "long", "mechanism"):
        samples = problems(split, 32)
        by_split[split] = {p.key for p in samples}
        assert len(by_split[split]) == 32
        for p in samples:
            # Only expressions produced by the study generator are evaluated in this independent test.
            assert eval(p.expression, {"__builtins__": {}}) == p.values[-1]
            assert partition(p) == split
        assert samples == problems(split, 32)
    assert len(set.union(*by_split.values())) == sum(map(len, by_split.values()))
    assert Problem.from_expression("(2+3)*4").key == Problem.from_expression("4*(3+2)").key
    assert shape(Problem.from_expression("(1+2)*(3+4)")) == "layout"


def test_published_steps_and_first_error_evidence_with_an_independent_interpreter():
    for problem in problems("train", 64):
        variables = {}
        for line in problem.steps:
            target, operation = line.split(" = ")
            # Only the trusted generator's published arithmetic is executed by this independent oracle.
            variables[target] = eval(operation, {"__builtins__": {}}, variables)
        reference = tuple(variables.values())
        assert reference == problem.values
        for first in range(len(reference)):
            faulty = reference[:first] + tuple(v + 1 for v in reference[first:])
            assert solver_truth(problem, render(faulty)) == (0, first+1, reference[first])


def test_transfer_mutates_only_the_evidence_and_changes_sign_and_absolute_magnitude():
    from study.judging import twin

    for i, problem in enumerate(problems("dev", 32)):
        trace, first, good, changed = twin(problem, i, transfer=True)
        original, altered = parse(good, 6), parse(changed, 6)
        assert original[:2] == altered[:2] and original[3:] == altered[3:]
        assert abs(altered[2]) > abs(original[2]) + 1
        assert original[2] == 0 or original[2] * altered[2] < 0
        assert expected(problem, trace, [first, changed])[:3] == (0, 3, original[2])


def test_run_dependencies_and_shuffled_signal():
    seen = set()
    for row in matrix():
        assert set(row.dependencies) <= seen
        assert row.name not in seen
        seen.add(row.name)
    assert {f"{arm}-{seed}" for arm in ("d2", "d3", "flat") for seed in (17, 29, 43)} <= seen
    values = [0, 1, 1, 0, 1, 1, 1, 1]
    shuffled = permute_groups(values, random.Random(17))
    assert sum(shuffled[:4]) == 2 and shuffled[4:] == values[4:]
    with pytest.raises(ValueError):
        permute_groups(values[:3], random.Random(17))
