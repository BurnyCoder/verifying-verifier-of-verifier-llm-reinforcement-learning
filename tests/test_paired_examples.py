"""Verify that paired examples keep checkpoints, raw reports and effective solver verdicts aligned."""

import pytest

from study.paired_examples import pair_saved_outputs, differing_examples, outcome_counts, output_table


def saved(key, trace, correct, bits):
    return dict(key=key, expression="(39 + 12) - 5", expected_values=[51, 46], trace=trace, correct=correct,
                malformed=False, reports=["1,0,46", "1,0,46,1,0,46", "0,2,46,1,0,46"], verdicts=bits)


def test_examples_use_recorded_solver_verdicts_and_show_both_checkpoints():
    shallow = [saved("a", "51,46", True, [1, 1, 1]), saved("b", "51,45", False, [1, 1, 1])]
    deep = [saved("a", "16,11", False, [1, 1, 1]), saved("b", "51,46", True, [1, 1, 1])]
    paired = pair_saved_outputs(shallow, deep)
    assert outcome_counts(paired) == {(1, 1): 1}
    assert differing_examples(paired) == paired
    table = output_table(paired)
    assert "51,46" in table and "16,11" in table and "0,2,46,1,0,46" in table
    assert "accept <code>0,2,46,1,0,46</code>" in table

    with pytest.raises(ValueError, match="same problem"):
        pair_saved_outputs(shallow, list(reversed(deep)))
