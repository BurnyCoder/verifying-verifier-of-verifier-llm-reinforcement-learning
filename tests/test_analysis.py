"""The registered interval pairs problems across arms and requires every seed."""

from study.analysis import paired_primary


def test_pooled_decision_waits_for_complete_matched_seeds():
    outcomes = {"d3-17": {"a": 1, "b": 1}, "d2-17": {"a": 0, "b": 1}}
    assert paired_primary(outcomes, required_n=2)["status"] == "pending"
    for seed in (29, 43):
        outcomes[f"d3-{seed}"] = {"a": 1, "b": 1}
        outcomes[f"d2-{seed}"] = {"a": 0, "b": 1}
    result = paired_primary(outcomes, required_n=2)
    assert result["delta"] == 0.5 and result["status"] == "inconclusive"
    outcomes["d2-43"] = {"a": 0, "c": 1}
    assert paired_primary(outcomes, required_n=2)["status"] == "pending"
