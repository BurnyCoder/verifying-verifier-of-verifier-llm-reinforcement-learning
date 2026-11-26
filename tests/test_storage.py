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
