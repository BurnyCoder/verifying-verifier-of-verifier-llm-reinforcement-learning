"""Separate sampled-answer divergence from a change of reward on fixed samples."""

from study.online_trajectory import trajectory_evidence


def test_direct_solver_timing_uses_only_the_actual_answers_and_rewards():
    from study.online_trajectory import cross_run_differences

    def run(answers, rewards):
        return [dict(expression="(2+3)-1",answer=a,reward=r) for a,r in zip(answers,rewards,strict=True)]
    left = run(["5,4"]*8,[1]*8)
    right = run(["4,3"]+["5,4"]*7,[1]*4+[0,1,1,1])
    found = cross_run_differences(iter(left),iter(right))
    assert (found["first_answer_difference"],found["first_credit_difference"])==(1,2)
    assert (found["same_answers"],found["different_credits"])==(1,1)


def test_constant_changes_have_no_relative_credit_and_sampled_answers_can_diverge_first():
    def group(outputs, bits, reviews):
        return [dict(expression="(2 + 3) - 1",answer=ans,label=int(ans=="5,4"),reward=reward,
                     reports=["1,0,4", f"1,0,4,{lower},0,4", f"1,0,4,{reward},0,4"])
                for ans,reward,lower in zip(outputs,bits,reviews,strict=True)]
    same = ["5,4"]*4
    wrong = ["5,4"]*3+["5,5"]
    ones, zeros = [1]*4, [0]*4
    a = group(same,ones,ones)+group(wrong,[1,1,1,0],[1,1,1,0])
    b = group(same,zeros,ones)+group(same,ones,ones)
    evidence = trajectory_evidence(a,b)
    assert evidence["first_answer_difference"]==evidence["first_credit_difference"]==2
    assert evidence["same_answers"]==1 and evidence["different_credits"]==1
    assert list(evidence["examples"])==["constant"]
    assert evidence["examples"]["constant"]["update"]==1
