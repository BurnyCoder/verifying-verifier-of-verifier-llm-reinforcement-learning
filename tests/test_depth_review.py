"""Check adjudication, group-relative credit and locally consistent arithmetic on toy traces."""

import pytest

from study.domain import Problem


def test_an_endorsed_rejection_and_an_invalid_audit_flag_both_reward_zero():
    from study.depth_review import effective_bit

    assert effective_bit("1,0,7,0,1,7") == 0
    assert effective_bit("-1,0,7,1,0,7") == 0
    assert effective_bit("0,2,7,1,0,7") == 1
    assert effective_bit("1,0,7,0,1") == 0


def test_arithmetic_diagnostic_separates_propagated_error_from_correct_final():
    from study.depth_review import trace_error

    p = Problem.from_expression("(39 + 12) - 5")
    assert trace_error(p, "51,46") == "correct"
    assert trace_error(p, "16,11") == "first wrong, second consistent"
    assert trace_error(p, "16,46") == "first wrong, second inconsistent"
    assert trace_error(p, "51,40") == "second wrong"
    assert trace_error(p, "46") == "format"


def test_earlier_judge_can_grade_same_group_better_while_aggregate_agreement_ties():
    from study.depth_review import group_evidence

    reports = lambda bit: f"1,0,7,{bit},0,7"
    deep = [dict(label=label, reports=["1,0,7", reports(second), reports(third)])
            for label, second, third in [(1,1,0), (0,0,1), (0,1,0), (0,1,0)]]
    result = group_evidence(deep)
    assert result["fixes"] == result["harms"] == 2
    assert result["changed_groups"] == 1
    assert result["j2_pairs"] == [1,2,0]
    assert result["j3_pairs"] == [0,2,1]
    assert result["same_answers_paid"] == [{"correct":1,"wrong":2},{"correct":0,"wrong":1}]


def test_group_evidence_rejects_an_incomplete_training_group():
    from study.depth_review import group_evidence

    with pytest.raises(ValueError, match="four"):
        group_evidence([{}])


def test_training_example_keeps_duplicate_samples_and_actual_terminal_rewards():
    from study.depth_review import group_evidence

    problem = "(18 - 11) - 3"
    group = [dict(step=19, expression=problem, answer=answer, label=y,
                  reports=["1,0,4", f"1,0,4,{y},0,4", f"1,0,4,{b},0,4"])
             for answer, y, b in [("7,4",1,0), ("7,4",1,1), ("5,2",0,0), ("5,2",0,1)]]
    example = group_evidence(group)["credit_example"]
    assert (example["expression"], example["update"]) == (problem, 20)
    assert example["samples"] == [["7,4",True,1,0], ["7,4",True,1,1], ["5,2",False,0,0], ["5,2",False,0,1]]


def test_actual_training_comparison_requires_identical_solver_text_and_lower_reports():
    from study.depth_review import compare_training_groups

    left = [dict(key="p", answer="7,4", reports=["1,0,4", "1,0,4,1,0,4"], reward=1)
            for _ in range(8)]
    right = [{**r, "reports": [*r["reports"], "1,0,4,1,0,4"]} for r in left]
    right[1]["reward"] = 0
    right[5]["reports"][1] = "1,0,7,1,0,4"
    assert compare_training_groups(left, right) == {"matched": [1], "different_credits": [1]}
    right[0]["answer"] = "7, 4"
    assert compare_training_groups(left, right) == {"matched": [], "different_credits": []}


def test_fixed_answer_replay_keeps_exact_grades_separate_from_judge_approvals():
    from study.depth_review import fixed_answer_replay

    problem = Problem.from_expression("(39 + 12) - 5")
    def replay(trace, correct, second, third):
        return dict(expression=problem.expression, trace=trace, correct=correct, expected_values=[51, 46],
                    verdicts=[1, second, third],
                    reports=["1,0,46", f"1,0,46,{second},0,46", f"1,0,46,{third},0,46"])

    # Both graders approve one answer. Their verdicts differ on both responses.
    cases = [replay("51,46", True, 0, 1), replay("16,11", False, 1, 0)]
    result = fixed_answer_replay(cases)
    assert (result["correct"], result["n"]) == (1, 2)
    assert result["accepted"] == [1, 1]
    assert result["agreement"] == [0, 2]
    assert (result["fixes"], result["harms"]) == (2, 0)
    assert [row["output"] for row in result["transitions"]] == ["51,46", "16,11"]

    cases[0]["verdicts"][2] = 0
    with pytest.raises(ValueError, match="logged verdicts"):
        fixed_answer_replay(cases)
