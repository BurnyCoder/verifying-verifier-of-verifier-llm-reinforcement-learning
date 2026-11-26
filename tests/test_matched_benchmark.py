"""Use artificial learning outcomes to test the amended experiment without opening predictions."""

import json
import os
import subprocess
import sys

import pytest

from study.storage import read_json, write_json


def test_freeze_requires_confirmed_learning_and_preserves_every_original_arm(tmp_path):
    from study.benchmark import freeze_profile
    from study.design import matrix

    calibration = tmp_path / "learnability"
    choice = {"family": "two-add", "style": "demonstrated"}
    write_json(calibration/"screen.json", {"selected": choice})
    write_json(calibration/"confirm.json", {"confirmed": True, "cell": choice})
    write_json(calibration/"learning.json", {"status": "complete", "demonstrated": False})
    write_json(tmp_path/"budget.json", {"updates": 256, "seconds_per_update": 35})
    with pytest.raises(RuntimeError, match="learning"):
        freeze_profile(tmp_path)
    assert not (tmp_path/"calibrated/profile.json").exists()
    write_json(calibration/"learning.json", {"status": "complete", "demonstrated": True})
    profile = freeze_profile(tmp_path)
    assert read_json(tmp_path/"calibrated/budget.json") == read_json(tmp_path/"budget.json")
    assert freeze_profile(tmp_path) == profile
    # A Git checkout or equivalent JSON serializer may change indentation or line endings.
    screening = calibration/"screen.json"
    screening.write_bytes(json.dumps(read_json(screening), sort_keys=True).encode()+b"\r\n")
    assert freeze_profile(tmp_path) == profile
    calibrated = matrix(profile)
    assert [(r.name, r.dependencies, r.reward, r.seed) for r in calibrated] == [
        (r.name, r.dependencies, r.reward, r.seed) for r in matrix({})]
    assert all(r.family == "two-add" and r.prompt_style == "demonstrated" for r in calibrated)
    write_json(calibration/"confirm.json", {"confirmed": True, "cell": {**choice, "style": "registered"}})
    with pytest.raises(RuntimeError):
        freeze_profile(tmp_path)


def test_calibrated_ids_are_distinct_and_one_step_has_enough_problems():
    from study.benchmark import population
    from study.curriculum import phase_for

    ids = lambda items: {p.key for p in items}
    profile = {"family": "one", "style": "demonstrated"}
    test = population(profile, "test", 2048)
    pairs = population(profile, "mechanism", 128)
    assert len(ids(test) | ids(pairs)) == 2176
    assert all(phase_for(p) == "benchmark" for p in (*test, *pairs))
    assert list(test[:128]) == list(population(profile, "test", 128))
    assert not ids(population(profile, "dev", 32)) & (ids(test) | ids(pairs))
    assert not ids(population(profile, "original-difficulty", 128)) & ids(test)
    assert population(profile, "layout", 8) is None


def test_scoped_cli_keeps_adapters_results_and_logs_separate(tmp_path):
    env = dict(os.environ, STUDY_TRACK="calibrated", STUDY_RESULTS=str(tmp_path/"r"),
               STUDY_STATE=str(tmp_path/"s"), PYTHONUTF8="1")
    program = ("import json; from study.storage import RESULTS, adapter, Journal; "
               "print(json.dumps([str(RESULTS),str(adapter('d3-17')),str(Journal('d3-17').path)]))")
    command = subprocess.run([sys.executable, "-c", program], cwd=tmp_path, env=env,
                             encoding="utf-8", capture_output=True, check=True)
    paths = [s.replace("\\", "/") for s in json.loads(command.stdout)]
    assert paths[0].endswith("/r/calibrated") and paths[1].endswith("/s/calibrated/runs/d3-17/adapter")
    assert "/logs/calibrated/d3-17/" in paths[2]


def test_default_report_reads_scoped_results_without_pooling_legacy_observations(tmp_path, monkeypatch):
    from study import report

    monkeypatch.setattr(report, "ORIGINAL_RESULTS", tmp_path)
    write_json(tmp_path/"d3-17/trained.json", {"updates": 256})
    write_json(tmp_path/"d3-17/development.json", {"weights": "legacy"})
    (tmp_path/"d3-17/replay.jsonl").write_text('{"correct":0}\n', encoding="utf-8")
    write_json(tmp_path/"calibrated/profile.json", {"family":"two-add", "style":"demonstrated"})
    write_json(tmp_path/"calibrated/d3-17/trained.json", {"updates": 24})
    collected = report.collect()
    assert collected["profile"]["family"] == "two-add"
    assert [(r["name"], r["updates"], r["dev_n"]) for r in collected["runs"]] == [("d3-17", 24, 0)]
    assert collected["original_development"] == [{"name":"d3-17", "correct":0, "n":1}]
    assert collected["primary"]["status"] == "pending"
