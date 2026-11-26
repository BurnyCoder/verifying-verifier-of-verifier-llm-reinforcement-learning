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
