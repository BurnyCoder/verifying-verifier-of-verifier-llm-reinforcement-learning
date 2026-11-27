"""The live transcript must retain full Unicode records from the solver and frozen-judge processes."""

import json

from study.online_logs import journal_batch


def test_stream_merges_processes_and_waits_for_a_complete_json_line(tmp_path):
    a = tmp_path/"solver.jsonl"
    b = tmp_path/"judges.jsonl"
    outputs = [json.dumps({"time":t,"text":txt},ensure_ascii=False).encode()+b"\n"
               for t,txt in (("01","2, 4"),("02","判断"),("03","entire output"*1200))]
    a.write_bytes(outputs[0]+outputs[2][:-1])
    b.write_bytes(outputs[1])
    offsets = {}
    assert list(journal_batch(tmp_path,offsets))==outputs[:2]
    with a.open("ab") as stream:
        stream.write(b"\n")
    assert list(journal_batch(tmp_path,offsets))==outputs[2:]
    assert list(journal_batch(tmp_path,offsets))==[]
