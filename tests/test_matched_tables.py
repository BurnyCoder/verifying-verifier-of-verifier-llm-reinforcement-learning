"""Verify that actual review depth, identical solver inputs and pending cells are preserved."""

import json

import pytest

from study.matched_tables import accuracy_grid, grid_markdown, shallow_feedback_note
from study.storage import write_json


def test_fitted_adapter_count_does_not_substitute_for_fewer_judge_calls(tmp_path):
    examples = [dict(key=str(i),expression=str(i),trace=str(i),expected_values=[i],correct=i%2,verdicts=[1,0,i%2],
                     reports=[f"1,0,{i}", f"1,0,{i},0,1,{i}", f"1,0,{i},{i%2},0,{i}"])
                for i in range(32)]
    def save(name,example_rows):
        target = tmp_path/name
        write_json(target/"development.json",{"phase":"development"})
        (target/"replay.jsonl").write_text("".join(json.dumps(r)+"\n" for r in example_rows),encoding="utf-8")
    for name in ("base","d1-17","d2-17","d3-17","exact-prefix1","exact-prefix2","exact-prefix3","exact-j1"):
        save(name,examples)
    grid, = accuracy_grid(tmp_path,{"family":"two-add"})
    assert grid["solver"][1][1:]==["Pending","Pending","16/32 (50.0%)"]
    assert grid["judge"][0][1:]==["16/32 (50.0%)","16/32 (50.0%)","32/32 (100.0%)"]
    assert "Three judges · J3 checks J2" in grid_markdown([grid])
    assert "Always accepting scores 16/32 (50.0%)" in grid_markdown([grid])
    assert "fixed Judge 2’s verdict on 16/32 answers and introduced a grading error on 0/32" in grid["judge_note"]
    assert len(grid["frozen_changes"]) == 16
    assert "Fixed a grading error" in grid_markdown([grid])
    save("exact-j1",[dict(r,trace="a different solution") for r in examples])
    with pytest.raises(ValueError,match="Unmatched solver responses"):
        accuracy_grid(tmp_path,{"family":"two-add"})


def test_identical_reward_check_distinguishes_same_total_from_same_assignments(tmp_path):
    a = [dict(key="p", step=0, sample=i, answer=str(i), reward=i%2) for i in range(4)]
    b = [{**r, "reward": 1-r["reward"]} for r in a]
    for arm, training in (("exact-depth1",a),("exact-depth2",b)):
        target = tmp_path/arm
        write_json(target/"development.json", {"phase":"development"})
        (target/"rollouts.jsonl").write_text("".join(json.dumps(r)+"\n" for r in training),encoding="utf-8")
        (target/"replay.jsonl").write_text(json.dumps(dict(key="q",expression="(1 + 1) + 1",trace="2,3"))+"\n",encoding="utf-8")
    note = shallow_feedback_note(tmp_path)
    assert "4/4 training completions" in note and "matched on 0/4" in note
    assert "2 and 2 positive rewards" in note and "1/1 development questions" in note
