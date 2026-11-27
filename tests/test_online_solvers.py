"""Verify the conditional cross-model experiment without querying a language model."""

from types import SimpleNamespace

import pytest

from study.domain import Problem
from study.storage import rows, write_json


def test_real_reward_callback_uses_external_terminal_solution_bit(tmp_path, monkeypatch):
    from study.online_solvers import score_chain
    from study.training import Reward
    from study import training
    from study.design import Run

    calls = []
    def ask(identifier, level, problem, trace, history):
        assert len(history) == level - 1
        calls.append((identifier, level, trace, history.copy()))
        return ["0,1,7", "1,0,7,0,1,7", "0,1,0,1,0,14"][level-1]

    solver = SimpleNamespace(journal=SimpleNamespace(event=lambda *args, **kw: None))
    monkeypatch.setattr(training, "RESULTS", tmp_path)
    batch = dict(prompts=["p"]*4, completions=["8,14"]*4, expression=["(4+3)*2"]*4,
                 trace=[""]*4, history_json=["[]"]*4, trainer_state=SimpleNamespace(global_step=0))
    for level in (2, 3):
        calls.clear()
        run = Run(f"new-judges/winner-d{level}", reward=f"d{level}")
        callback = Reward(solver, run, lambda ps, ts, d, step: score_chain(ask, ps, ts, d, step))
        assert callback(**batch) == [int(level == 3)]*4
        assert len(set(c[0] for c in calls)) == 4*level
        records = list(rows(tmp_path/run.name/"rollouts.jsonl"))
        assert all(r["label"] == 0 and len(r["reports"]) == level for r in records)


def test_online_gate_rejects_artifact_drift_and_closed_gate(tmp_path):
    from study.online_solvers import selected_judge
    from study.frozen_models import MODELS
    from study.frozen_gpu import BUILD, CONTEXT, LIMIT

    model = next(m for m in MODELS if m.key == "q35-4b")
    root = tmp_path/"new-judges"
    write_json(root/"decision.json", dict(online_gate=False, selected=model.key))
    with pytest.raises(ValueError, match="gate"):
        selected_judge(root)
    write_json(root/"decision.json", dict(online_gate=True, selected=model.key))
    config = dict(model=model.title, repository=model.repository, revision=model.revision, file=model.filename,
                  sha256=model.sha256, base_revision=model.base_revision, build=BUILD, context=CONTEXT,
                  output_limit=LIMIT, placement="CUDA0", decoder="greedy, thinking disabled, raw generated tokens")
    write_json(root/"confirm-winner/configuration.json", config)
    assert selected_judge(root) == model
    write_json(root/"confirm-winner/configuration.json", {**config, "sha256":"different"})
    with pytest.raises(ValueError, match="configuration"):
        selected_judge(root)


def test_online_dev_exact_scorer_rejects_broken_pairs(tmp_path):
    from study.online_report import exact_scores
    from study.storage import append
    problem = Problem.from_expression("(4+3)*2")
    path = tmp_path/"answers.jsonl"
    record = dict(key=problem.key, expression=problem.expression, trace="8,14", correct=0)
    append(path, record)
    assert exact_scores(path, [problem.key]) == {problem.key:0}
    append(path, record)
    with pytest.raises(ValueError, match="IDs"):
        exact_scores(path, [problem.key])
    path.unlink()
    append(path, {**record, "correct":1})
    with pytest.raises(ValueError, match="exact"):
        exact_scores(path, [problem.key])
