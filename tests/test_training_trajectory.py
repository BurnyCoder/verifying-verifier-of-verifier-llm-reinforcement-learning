"""Verify that windowed reward counts distinguish wrong answers paid from truly correct work."""

from study.trajectory import training_quarters


def test_training_quarters_grade_current_answers_and_replay_the_same_lower_verdict():
    training = []
    for step in range(4):
        for label, paid, lower in [(1, 0, 1), (1, 1, 1), (0, 0, 0), (0, 1, 0)]:
            training.append(dict(step=step, label=label, reward=paid, reports=["1,0,4", f"1,0,4,{lower},0,4"]))
    windows = training_quarters(training)
    assert [r["first_update"] for r in windows] == [1, 2, 3, 4]
    assert windows[-1] == dict(first_update=4, last_update=4, n=4, correct=2, rewarded_correct=1,
                               rewarded_wrong=1, j2_rewarded_correct=2, j2_rewarded_wrong=0)
