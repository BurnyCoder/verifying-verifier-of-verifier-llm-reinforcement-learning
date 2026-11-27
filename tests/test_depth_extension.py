"""Verify the additional four treatments use the registered solver path at their actual depths."""

import pytest


def test_extra_solvers_reuse_the_deep_conditions_except_for_terminal_depth():
    from dataclasses import replace
    from study.design import matched_runs, matrix

    profile={"family":"two-add","style":"demonstrated"}
    original={r.name:r for r in matrix(profile)}
    extra=matched_runs(profile)
    assert len(extra)==4 and len(original)==32 and not matched_runs({})
    for spec in extra:
        route,depth=spec.name.split("-depth")
        deep=original[route+"-prefix3"]
        assert spec==replace(deep,name=spec.name,reward="d"+depth)


def test_fixed_stack_requires_persisted_identical_solver_answers(tmp_path,monkeypatch):
    evaluate=pytest.importorskip("study.evaluate")
    from study.domain import Problem
    from study.storage import append,write_json

    monkeypatch.setattr(evaluate,"RESULTS",tmp_path)
    monkeypatch.setattr(evaluate,"active_profile",lambda: {"family":"two-add","style":"demonstrated"})
    write_json(tmp_path/"base/development.json",{"phase":"development"})
    problems=[Problem.from_expression(f"({i}+3)-2") for i in range(32)]
    monkeypatch.setattr(evaluate,"population",lambda *args:problems)
    for p in problems[:-1]:
        append(tmp_path/"base/replay.jsonl",dict(key=p.key,expression=p.expression,trace="wrong"))
    with pytest.raises(ValueError,match="complete saved"):
        evaluate.stack_replay("exact")


def test_fitted_stack_scores_all_prefixes_without_resampling_solver_or_adding_ballots(tmp_path,monkeypatch):
    evaluate=pytest.importorskip("study.evaluate")
    from study.design import ROUTES
    from study.domain import Problem
    from study.records import expected,render
    from study.storage import append,read_json,rows,write_json

    pset=[Problem.from_expression(f"({i}+3)-2") for i in range(32)]
    calls=[]
    class Frozen:
        def __init__(self,journal,frozen):
            assert tuple(frozen)==ROUTES["exact"]
            self.totals={}
        def prompt(self,role,p,trace,history):
            return (p,trace,history)
        def generate(self,prompts,snapshot,role,seed,sample):
            calls.append(role)
            assert sample and snapshot=="exact-"+role
            return [render(expected(p,trace,history)) for p,trace,history in prompts]
    monkeypatch.setattr(evaluate,"RESULTS",tmp_path)
    monkeypatch.setattr(evaluate,"active_profile",lambda:{"family":"two-add","style":"demonstrated"})
    monkeypatch.setattr(evaluate,"population",lambda *args:pset)
    monkeypatch.setattr(evaluate,"Backend",Frozen)
    monkeypatch.setattr(evaluate,"weights_digest",lambda key:"hash-"+key)
    monkeypatch.setattr(evaluate,"generation_cost",lambda name,totals:{"usage":totals})
    write_json(tmp_path/"base/development.json",{"phase":"development"})
    for i,p in enumerate(pset):
        trace=render(p.values) if i%2 else "an invalid answer"
        append(tmp_path/"base/replay.jsonl",dict(key=p.key,expression=p.expression,trace=trace,correct=i%2))
    evaluate.stack_replay("exact")
    result=list(rows(tmp_path/"matched-depth/exact-development.jsonl"))
    assert calls==["j1","j2","j3"]*4 and len(result)==32
    assert all(r["verdicts"]==[r["correct"]]*3 and not r["votes"] for r in result)
    assert read_json(tmp_path/"matched-depth/exact-development.json")["n"]==32
    evaluate.stack_replay("exact")
    assert len(calls)==12
