"""Verify monitoring uses measured elapsed time and leaves held-out outcomes undisclosed."""

from study.storage import append, write_json


def test_training_progress_uses_saved_optimizer_time(tmp_path, monkeypatch):
    from study import monitor

    monkeypatch.setattr(monitor, "RESULTS", tmp_path/"results")
    monkeypatch.setattr(monitor, "ROOT", tmp_path)
    target=tmp_path/"results/d3-17"
    write_json(target/"recipe.json", {"updates": 256})
    append(target/"cost.jsonl", {"step": 32, "elapsed_seconds": 1280})
    update=monitor.inspect_worker("d3-17","train",elapsed=1300)
    assert update["remaining_seconds"] == 224*40
    assert update["next_check_seconds"] == 1800
    assert "32 of 256" in (tmp_path/"reports/progress.md").read_text(encoding="utf-8")
    assert [monitor.cadence(x) for x in (1200,2700,7200)] == [300,900,1800]


def test_final_monitor_counts_committed_rows_without_releasing_values(tmp_path,monkeypatch):
    from study import monitor

    monkeypatch.setattr(monitor,"RESULTS",tmp_path/"results")
    monkeypatch.setattr(monitor,"ROOT",tmp_path)
    append(tmp_path/"results/base/test.jsonl",{"key":"sample-private","correct":1,"trace":"secret-example"})
    update=monitor.inspect_worker("base","final",elapsed=800)
    assert update["records"] == {"test":1}
    assert "sample-private" not in repr(update) and "secret-example" not in repr(update)


def test_transient_publication_retries_the_same_milestone(monkeypatch):
    import subprocess
    from study import cli

    calls, waits = [], []
    def publish(command):
        calls.append(command)
        return subprocess.CompletedProcess(command, 1 if len(calls)==1 else 0)
    monkeypatch.setattr(cli.subprocess,"run",publish)
    monkeypatch.setattr(cli.time,"sleep",waits.append)
    cli.worker("publish","--milestone","example")
    assert len(calls)==2 and calls[0]==calls[1] and waits==[15]
