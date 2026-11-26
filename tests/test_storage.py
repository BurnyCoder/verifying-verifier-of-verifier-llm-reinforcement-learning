"""A restart must preserve completed observations and discard an incomplete final record."""

from study.storage import append, rows


def test_torn_unicode_record_is_repaired_before_the_next_observation(tmp_path):
    path=tmp_path/"trace.jsonl"
    append(path,{"sample":"first"})
    with path.open("ab") as file:
        file.write(b'{"sample":"'+b"x"*70000+b"\xe2")
    assert list(rows(path))==[{"sample":"first"}]
    append(path,{"sample":"next"})
    assert list(rows(path))==[{"sample":"first"},{"sample":"next"}]


def test_published_text_uses_git_line_endings(tmp_path):
    from study.storage import atomic
    target = tmp_path / "receipt.json"
    atomic(target, "first\nsecond\n")
    assert target.read_bytes() == b"first\nsecond\n"


def test_redirected_windows_terminal_preserves_model_unicode(tmp_path):
    import os
    import subprocess
    import sys

    program = "from study.storage import Journal; Journal('utf8').event('output_chunk',text=chr(0x2212))"
    result = subprocess.run([sys.executable,"-c",program],cwd=tmp_path,capture_output=True,
                            env={**os.environ,"PYTHONIOENCODING":"cp1252"},check=True)
    assert "−" in result.stdout.decode("utf-8")
    log = next((tmp_path/"logs/utf8").glob("*.jsonl"))
    assert next(rows(log))["text"]=="−"


def test_generation_cost_includes_completed_attempts_before_evaluation_resume(tmp_path,monkeypatch):
    from study import storage
    monkeypatch.setattr(storage,"ROOT",tmp_path)
    for name in ("first","resumed"):
        path=tmp_path/"logs/run"/(name+".jsonl")
        append(path, dict(event="prompts",role="j3"))
        append(path, dict(event="outputs",role="j3",calls=8,input_tokens=20,output_tokens=16,gpu_seconds=4,wall_seconds=5))
    append(tmp_path/"logs/run/first.jsonl",dict(event="prompts",role="j3"))
    cost=storage.generation_cost("run",{})
    assert cost["usage"]["j3"]==dict(calls=16,input_tokens=40,output_tokens=32,gpu_seconds=8,wall_seconds=10)
    assert cost["unfinished_generation_batches"]==1
