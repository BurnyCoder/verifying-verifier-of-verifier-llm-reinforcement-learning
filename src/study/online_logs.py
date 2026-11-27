"""Serve the complete timestamped solver and judge journals for a named online training run."""

import heapq
import json
import time
from contextlib import ExitStack

from .storage import ORIGINAL_RESULTS, log_directory


def journal_batch(directory, offsets):
    """Interleave complete JSONL records by timestamp. Keep the byte offset of each journal."""
    def available(stream, path):
        stream.seek(offsets.get(path, 0))
        while raw := stream.readline():
            if not raw.endswith(b"\n"):
                return
            offsets[path] = stream.tell()
            yield json.loads(raw)["time"], raw

    with ExitStack() as opened:
        streams = [available(opened.enter_context(path.open("rb")), path)
                   for path in sorted(directory.glob("*.jsonl"))]
        for _,raw in heapq.merge(*streams):
            yield raw


def serve_transcript(handler, name):
    """Follow both processes until training finishes, the reader leaves, or a worker stays silent."""
    directory = log_directory()/name
    if not directory.is_dir():
        handler.send_error(404, "Training has not started")
        return
    handler.send_response(200)
    handler.send_header("Content-Type","text/plain; charset=utf-8")
    handler.send_header("Cache-Control","no-store")
    handler.send_header("Connection","close")
    handler.end_headers()
    offsets = {}
    last_write = time.monotonic()
    try:
        while True:
            finished = (ORIGINAL_RESULTS/name/"trained.json").is_file()
            for record in journal_batch(directory, offsets):
                handler.wfile.write(record)
                last_write = time.monotonic()
            handler.wfile.flush()
            if finished or time.monotonic()-last_write>90:
                return
            time.sleep(1)
    except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
        return
