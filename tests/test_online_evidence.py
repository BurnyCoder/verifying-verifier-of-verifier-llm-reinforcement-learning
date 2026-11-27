"""Verify that the direct-judge comparison uses paired literal answers and group-relative rewards."""

from study.domain import Problem


def test_fixed_training_groups_count_repaired_and_harmed_verdicts_separately():
    from study.online_evidence import audit_intervention

    def group(direct, reviewed, truth):
        return [dict(reports=[f"{a},0,7", f"1,0,7,{b},0,7"],label=v)
                for a,b,v in zip(direct,reviewed,truth,strict=True)]
    constant = group([0]*4,[1]*4,[1,1,1,0])
    mixed = group([0,1,0,1],[0,0,1,1],[0,0,1,1])
    assert audit_intervention(constant+mixed, 1, 2) == dict(
        samples=8, groups=2, fixed=5, harmed=1, changed_credit_groups=1)


def test_examples_choose_first_shared_problem_per_observed_accuracy_pattern():
    from study.online_evidence import paired_examples

    problems = [Problem.from_expression(f"(4+3)*{i}") for i in (2,3,4)]
    cohorts = []
    for correct in ([True,True,False],[False,False,True],[True,True,True]):
        cohorts.append([dict(key=p.key,expression=p.expression,valid=int(v),trace="literal",reports=["a","b","c"])
                        for p,v in zip(problems,correct,strict=True)])
    examples = paired_examples(cohorts)
    assert [r["key"] for r in examples]==[problems[0].key,problems[2].key]
    assert examples[0]["expected"]==[7,14]
    assert examples[0]["correct"]==[1,0,1]
    assert examples[0]["reports"]==[["a","b","c"]]*3
