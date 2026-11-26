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
