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


def test_flat_contrast_reports_paired_seed_intervals_without_a_primary_decision():
    from study.analysis import paired_comparison

    outcomes = {}
    for seed in (17, 29, 43):
        outcomes[f"d3-{seed}"] = {"x": 1, "y": 1}
        outcomes[f"flat-{seed}"] = {"x": 0, "y": 0}
    estimate = paired_comparison(outcomes, "flat", required_n=2)
    assert estimate["status"] == "estimated"
    assert estimate["ci"] == [1, 1]
    assert estimate["seed_intervals"] == {str(seed): [1, 1] for seed in (17, 29, 43)}


def test_replay_errors_include_the_population_at_risk_and_independent_ballots():
    from study.analysis import replay_metrics

    sample = [
        {"correct": 0, "verdicts": [0, 0, 1], "flat": 0, "judge_malformed": [False]*3,
         "votes": ["bad", "0,1,7", "0,1,7"], "full_report_correct": [0, 0, 0]},
        {"correct": 1, "verdicts": [1, 0, 1], "flat": 1, "judge_malformed": [False, True, False],
         "votes": ["1,0,9", "1,0,9", "1,0,9"], "full_report_correct": [1, 0, 1]},
    ]
    methods = {row["method"]: row for row in replay_metrics(sample)}
    assert methods["D3"]["false_accept"] == methods["D3"]["invalid"] == 1
    assert methods["D2"]["false_reject"] == methods["D2"]["valid"] == 1
    assert methods["Flat"]["malformed"] == 1 and methods["Flat"]["reports"] == 6
