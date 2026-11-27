"""Verify that actual review depth, identical solver inputs and pending cells are preserved."""

import json

import pytest

from study.matched_tables import accuracy_grid, grid_markdown
from study.storage import write_json


def test_fitted_adapter_count_does_not_substitute_for_fewer_judge_calls(tmp_path):
    examples = [dict(key=str(i),expression=str(i),trace=str(i),correct=i%2,verdicts=[1,0,i%2],reports=["a","b","c"])
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
    save("exact-j1",[dict(r,trace="a different solution") for r in examples])
    with pytest.raises(ValueError,match="Unmatched solver responses"):
        accuracy_grid(tmp_path,{"family":"two-add"})
