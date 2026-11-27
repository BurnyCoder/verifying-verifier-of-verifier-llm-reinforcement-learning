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
