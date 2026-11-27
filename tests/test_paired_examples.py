"""Verify that paired examples keep checkpoints, raw reports and effective solver verdicts aligned."""

import pytest

from study.paired_examples import pair_saved_outputs, differing_examples, outcome_counts, output_table, report_key, explain_report


def saved(key, trace, correct, bits):
    return dict(key=key, expression="(39 + 12) - 5", expected_values=[51, 46], trace=trace, correct=correct,
                malformed=False, reports=["1,0,46", "1,0,46,1,0,46", "0,2,46,1,0,46"], verdicts=bits)


def test_examples_use_recorded_solver_verdicts_and_show_both_checkpoints():
    shallow = [saved("a", "51,46", True, [1, 1, 1]), saved("b", "51,45", False, [1, 1, 1])]
    deep = [saved("a", "16,11", False, [1, 1, 1]), saved("b", "51,46", True, [1, 1, 1])]
    deep[0]["reports"][0] = "1,0,16"
    paired = pair_saved_outputs(shallow, deep)
    assert outcome_counts(paired) == {(1, 1): 1}
    assert differing_examples(paired) == paired
    table = output_table(paired)
    assert "51,46" in table and "16,11" in table and "0,2,46,1,0,46" in table
    assert "Flags field 2 of Judge 2 and proposes 46. Accepts the solver and gives 46 as its final value." in table
    key = report_key(paired)
    assert "1,0,46" in key and "final value is 46" in key
    assert "0,1,51" in key and "step 1 should be 51" in key
    assert "final value is 16" in key and "own final value was 11" in key

    with pytest.raises(ValueError, match="same problem"):
        pair_saved_outputs(shallow, list(reversed(deep)))


def test_explained_critic_can_endorse_a_review_and_still_reject_the_solver():
    assert explain_report("1,0,15,0,1,15", 3, 0).startswith(
        "Endorses Judge 2 and supports the value 15. Rejects the solver and says step 1 should be 15.")
    assert "Invalid review flag -1" in explain_report("-1,-1,-5,1,0,-5", 2, 0)
    assert "effective verdict is reject" in explain_report("-1,-1,-5,1,0,-5", 2, 0)
    with pytest.raises(ValueError, match="effective verdict"):
        explain_report("1,0,46", 1, 0)
