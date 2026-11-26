"""Use artificial outcomes to test curriculum isolation, selection and learning claims."""

from study.domain import partition, problems


def test_difficulty_families_hold_related_variants_in_one_disjoint_partition():
    from study.curriculum import FAMILIES, curriculum_problems, phase_for

    original={p.key for p in problems("train",256)}
    splits={}
    for phase in ("screen","confirm","train","validation","benchmark"):
        keys=set()
        for family in FAMILIES:
            batch=curriculum_problems(family,phase,18)
            assert len({p.key for p in batch})==18
            assert all(partition(p)=="train" and phase_for(p)==phase for p in batch)
            if family=="one":
                assert all(len(p.values)==1 for p in batch)
            keys.update(p.key for p in batch)
        assert not keys & original and all(not keys & previous for previous in splits.values())
        splits[phase]=keys


def test_cell_selection_excludes_aggregate_accuracy_without_mixed_groups():
    from study.learnability_analysis import choose_cell

    def cell(family,rate,mixed,parsed=1.0):
        return dict(family=family,style="demonstrated",sampled_exact=rate,greedy_exact=rate,
                    mixed_groups=mixed,problems=16,parsed=parsed)
    options=[cell("one",.5,0),cell("two-add",.45,6),cell("two-mixed",.6,4),cell("registered",.5,6,.5)]
    assert choose_cell(options)["family"]=="two-add"
    assert choose_cell([options[0]]) is None


def test_demonstrations_leave_target_values_out_of_the_last_user_message():
    from study.domain import Problem
    from study.prompts import messages
    p=Problem.from_expression("137+119")
    for role,prior in (("solver",[]),("j1",[]),("j2",["bad"]),("j3",["bad","bad"])):
        turns=messages(role,p,"0",prior,style="demonstrated")
        assert turns[-1]["role"]=="user" and "256" not in turns[-1]["content"]
        assert any(t["role"]=="assistant" for t in turns[:-1])


def test_learning_requires_paired_improvement_on_new_problems():
    from study.learnability_analysis import learning_result

    baseline={str(i):0 for i in range(256)}
    perfect={k:1 for k in baseline}
    positive=learning_result(baseline,perfect,baseline)
    assert positive["demonstrated"] and positive["reward_specific"]
    assert positive["over_base"]["interval"]==[1,1]
    assert not learning_result(perfect,perfect,baseline)["demonstrated"]
    assert learning_result(baseline,dict(list(perfect.items())[:-1]),baseline)["status"]=="pending"


def test_arithmetic_and_format_transitions_account_for_every_matched_gain():
    from study.learnability_analysis import changes_by_parse

    def row(parsed, correct):
        return dict(parsed=parsed, correct=correct, expression="2+3", trace="5" if correct else "wrong",
                    expected_values=[5])
    before=[row(1,0),row(1,1),row(0,0),row(1,1),row(0,0),row(0,0)]
    after =[row(1,1),row(1,0),row(1,1),row(0,0),row(0,0),row(1,1)]
    result = changes_by_parse(dict(enumerate(after)), dict(enumerate(before)))
    assert [(group["n"], group["gains"], group["losses"]) for group in result["groups"]] == [
        (2,1,1), (2,2,0), (1,0,1), (1,0,0)]
    assert [(e["stratum"], e["change"], e["key"]) for e in result["examples"]] == [
        ("Both parsed","gain",0),("Both parsed","loss",1),("Only trained parsed","gain",2),
        ("Only comparator parsed","loss",3)]


def test_learnability_report_regenerates_arithmetic_examples_from_validation_files(tmp_path,monkeypatch):
    import pytest
    learner=pytest.importorskip("study.learnability")
    from study.design import PILOTS
    from study.learnability_report import collect_learnability, learnability_text
    from study.storage import append, write_json

    monkeypatch.setattr(learner,"RESULTS",tmp_path)
    root = tmp_path/"learnability"
    write_json(root/"screen.json", {"cells":[], "selected":{"family":"one","style":"demonstrated"}})
    for name in ("base", *PILOTS):
        hits = 0
        for i in range(256):
            correct = name == PILOTS[0] or i % 4 == 0
            parsed = correct or i % 2 == 0
            hits += correct
            append(root/"evaluations"/(name+".jsonl"),
                   dict(key=str(i),correct=int(correct),parsed=parsed,trace="5" if correct else "6" if parsed else "<wrong>",
                        expected_values=[5],expression="2+3"))
        write_json(root/"evaluations"/(name+".json"), {"n":256, "parsed":256 if name==PILOTS[0] else 128,"correct":hits})
    outcome=learner.compare()
    assert outcome["reward_specific"] and outcome["over_base"]["fixed"]==192
    assert sum(g["gains"] for g in outcome["by_parse"]["base"]["groups"])==192
    text=learnability_text(collect_learnability(tmp_path))
    assert "Both parsed | 128 | 64 | 0" in text and "&lt;wrong&gt;" in text


def test_frozen_screen_confirmation_and_resume_with_an_artificial_backend(tmp_path,monkeypatch):
    import pytest
    learner=pytest.importorskip("study.learnability")
    from study.records import render
    calls=[]

    class Fixture:
        def __init__(self,journal):
            self.totals={}
        def prompt(self,role,p):
            return p
        def generate(self,prompts,snapshot,label,seed,sample):
            calls.append(label)
            if self.prompt_style=="registered":
                return ["bad"]*len(prompts)
            answers=[]
            for i,p in enumerate(prompts):
                values=list(p.values)
                if (sample and i%4>=2) or (not sample and i%2):
                    values[0]+=1
                answers.append(render(values))
            return answers

    monkeypatch.setattr(learner,"RESULTS",tmp_path)
    monkeypatch.setattr(learner,"Backend",Fixture)
    result=learner.screen()
    assert len(result["cells"])==8 and result["selected"]["style"]=="demonstrated"
    first=len(calls)
    assert learner.screen()==result and len(calls)==first
    assert learner.confirm()["confirmed"]
    assert learner.pilot_spec("learn-shuffle-17").reward=="oracle-shuffle"
