"""Use invented observations to challenge the release audit without opening sealed data."""

import pytest

from study.domain import Problem
from study.storage import append


def test_last_integer_cannot_hide_a_bad_intermediate_or_a_repeated_problem(tmp_path):
    from study.final_review import grade_solutions

    p = Problem.from_expression("(4 + 3) * 2")
    pool = {p.key: p}
    row = dict(key=p.key, expression=p.expression, problem=list(p.steps), split="test", trace="8,14",
               expected_values=[7, 14], malformed=False, final_correct=1, correct=0)
    path = tmp_path / "test.jsonl"
    append(path, row)
    assert grade_solutions(path, pool, "test") == {p.key: 0}
    append(path, row)
    with pytest.raises(ValueError, match="Duplicate"):
        grade_solutions(path, pool, "test")
    wrong = tmp_path / "wrong.jsonl"
    append(wrong, dict(row, correct=1))
    with pytest.raises(ValueError, match="grade"):
        grade_solutions(wrong, pool, "test")


def test_evidence_twin_requires_a_numerical_intervention_and_an_exact_repair(tmp_path):
    from study.final_review import grade_twins

    p = Problem.from_expression("(4 + 3) * 2")
    pool = {p.key: p}
    row = dict(key=p.key, expression=p.expression, split="mechanism", trace="8,14", first="0,1,7",
               reviews=["1,0,7,0,1,7", "1,0,6,0,1,7"], labels=[[1,0,7,0,1,7],[0,3,7,0,1,7]],
               visible=["1,0,7,0,1,7","0,3,6,0,1,7"], masked=["bad","bad"], visible_pair=0, masked_pair=0)
    path = tmp_path / "twins.jsonl"
    append(path, row)
    assert grade_twins(path, pool, "mechanism", novel=False) == 1
    with pytest.raises(ValueError, match="intervention"):
        grade_twins(path, pool, "mechanism", novel=True)
    altered = tmp_path / "wrong.jsonl"
    append(altered, dict(row, visible_pair=1))
    with pytest.raises(ValueError, match="pair grade"):
        grade_twins(altered, pool, "mechanism", novel=False)


def test_review_waits_for_completed_campaign_before_accessing_any_evaluation(tmp_path):
    from study.final_review import review_completed

    assert review_completed(tmp_path, {}) is None


def test_complete_audit_uses_fake_populations_and_rejects_prior_exposure(tmp_path,monkeypatch):
    """Run the full review using invented final cohorts, including natural and shared evidence rows."""
    import json
    import shutil
    from study import final_review
    from study.design import SEEDS, matrix
    from study.exposures import check_exposures
    from study.judging import twin
    from study.records import expected, render
    from study.storage import write_json

    sizes = dict(test=2048,layout=128,long=128,mechanism=128)
    pools = {split:[Problem.from_expression(f"({10000*(i+1)+j} + 1) - 2") for j in range(n)]
             for i,(split,n) in enumerate(sizes.items())}
    monkeypatch.setattr(final_review,"population",lambda profile,split,n: pools[split][:n])
    selected = {f"{arm}-{s}" for arm in ("d2","d3","flat") for s in SEEDS} | {"d1-17","exact-j3","exact-prefix3"}
    schedule = [r for r in matrix({}) if r.name in selected]
    monkeypatch.setattr(final_review,"matrix",lambda _: schedule)
    root = tmp_path/"results"
    fixtures = tmp_path/"invented"
    fixtures.mkdir()
    def save(name,records):
        with (fixtures/(name+".jsonl")).open("w",encoding="utf-8") as file:
            for record in records:
                file.write(json.dumps(record)+"\n")
    def solution(p,split):
        t = render(p.values)
        history = []
        for _ in range(3):
            history.append(render(expected(p,t,history)))
        return dict(key=p.key,expression=p.expression,split=split,trace=t,expected_values=p.values,
                    problem=p.steps,correct=1,final_correct=1,malformed=False,reports=history,
                    votes=[history[0]]*3,flat=1,full_report_correct=[1]*3,verdicts=[1]*3,fixed=0,harmed=0)
    def evidence(p,index,split,novel):
        trace,first,good,bad = twin(p,index,novel)
        reviews = [good,bad] if index%2 else [bad,good]
        labels = [expected(p,trace,[first,report]) for report in reviews]
        return dict(key=p.key,expression=p.expression,split=split,trace=trace,first=first,reviews=reviews,
                    labels=labels,visible=list(map(render,labels)),masked=["bad"]*2,visible_pair=1,masked_pair=0)
    for split in ("test","layout","long"):
        save(split,(solution(p,split) for p in pools[split]))
    save("judge-test",(solution(p,"test") for p in pools["test"][:128]))
    cells = (("mechanism","mechanism",False),("unseen-evidence","mechanism",True),
             ("layout-evidence","layout",False),("transfer-evidence","layout",True))
    for filename,split,novel in cells:
        save(filename,(evidence(p,i,split,novel) for i,p in enumerate(pools[split])))
    weight_ids = {r.name:"fixture-"+r.name for r in schedule}
    for name,role in [("base","solver"),*((r.name,r.role) for r in schedule)]:
        directory = root/name
        weight = weight_ids.get(name,"frozen base")
        write_json(directory/"development.json",dict(weights=weight,time="2026-01-01T10:00:00+00:00"))
        if name!="base":
            write_json(directory/"trained.json",dict(updates=1))
            for sample in range(4):
                append(directory/"rollouts.jsonl",dict(role=role,key="training-only",step=0,sample=sample,trace="",prior=[]))
        names = ["test","layout","long"] if role=="solver" else []
        if name in ("base","d3-17","exact-j3"):
            names.append("judge-test")
        sources = {}
        if name in ("base","exact-j3","exact-prefix3"):
            names.extend(f for f,_,_ in cells)
            sources = {f+".jsonl":("exact-j3" if name=="exact-prefix3" else name) for f,_,_ in cells}
        for file in names:
            shutil.copyfile(fixtures/(file+".jsonl"),directory/(file+".jsonl"))
        write_json(directory/"final.json",dict(weights=weight,time="2026-01-01T12:00:00+00:00",evidence_sources=sources))
    write_json(root/"seal.json",dict(time="2026-01-01T11:00:00+00:00",weights=weight_ids,
                                     ordered_training_exposures=check_exposures(root,schedule)))
    data = dict(completed=True,profile={},primary={"per_seed":{str(s):0 for s in SEEDS}},
                flat={"per_seed":{str(s):0 for s in SEEDS}})
    audit = final_review.review_completed(root,data)
    assert audit["overlap"]==0 and audit["test_ids"]==2432 and audit["natural_reviews"]==3*128
    assert audit["paired_records"]==3*4*128 and audit["distinct_paired_records"]==2*4*128
    assert len(audit["comparisons"])==7
    append(root/"base/replay.jsonl",{"key":pools["test"][0].key})
    with pytest.raises(ValueError,match="previously observed"):
        final_review.review_completed(root,data)
