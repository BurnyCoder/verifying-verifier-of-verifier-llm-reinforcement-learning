"""Verify that the test seal detects incomplete or unmatched training groups."""

import pytest

from study.design import Run
from study.storage import append, write_json


def test_comparison_requires_matched_training_exposures(tmp_path):
    from study.exposures import check_exposures

    specs = [Run("deep"), Run("shallow", reward="d2")]
    for spec in specs:
        write_json(tmp_path/spec.name/"trained.json", {"updates": 1})
        for sample in range(4):
            append(tmp_path/spec.name/"rollouts.jsonl",
                   dict(step=0, sample=sample, key="p", role="solver", trace="", prior=[]))
    signatures = check_exposures(tmp_path, specs)
    assert signatures["deep"] == signatures["shallow"]
    path = tmp_path/"shallow/rollouts.jsonl"
    text = path.read_text(encoding="utf-8")
    path.write_text(text.replace('"p"', '"q"'), encoding="utf-8")
    with pytest.raises(RuntimeError, match="order or preceding evidence"):
        check_exposures(tmp_path, specs)
    path.write_text(text.splitlines()[0]+"\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="Incomplete"):
        check_exposures(tmp_path, specs)
