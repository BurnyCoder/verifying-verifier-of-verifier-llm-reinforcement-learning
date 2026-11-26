"""Atomic run metadata and append-only JSONL observations for a single study checkout."""

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path.cwd()
load_dotenv(ROOT / ".env")
STATE = Path(os.environ.get("STUDY_STATE", ROOT / "checkpoints")).resolve()
RESULTS = Path(os.environ.get("STUDY_RESULTS", ROOT / "results")).resolve()


def stamp():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def atomic(path, content):
    """Replace a complete file in one operation so readers never see half a publication."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".{os.getpid()}.partial")
    temporary.write_text(content, encoding="utf-8")
    for attempt in range(6):
        try:
            os.replace(temporary, path)
            return
        except PermissionError:
            if attempt == 5:
                raise
            time.sleep(0.1 * (attempt + 1))


def write_json(path, value):
    atomic(path, json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def read_json(path, default=None):
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else default


def append(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(value, ensure_ascii=False, allow_nan=False) + "\n")


def rows(path):
    """Recover complete lines after interruptions. Reject corruption inside a closed record."""
    if path.is_file():
        with path.open(encoding="utf-8") as file:
            for line in file:
                if line.endswith("\n") and line.strip():
                    yield json.loads(line)


def retain(path, predicate):
    if path.exists():
        data = [json.dumps(row, ensure_ascii=False) for row in rows(path) if predicate(row)]
        atomic(path, "".join(line + "\n" for line in data))


class Journal:
    """Mirror complete public model inputs and outputs to a timestamped log and terminal."""

    def __init__(self, run):
        self.run = run
        self.path = ROOT / "logs" / run / (stamp().replace(":", "-") + ".jsonl")

    def event(self, event, **values):
        record = {"time": stamp(), "run": self.run, "event": event, **values}
        append(self.path, record)
        print(json.dumps(record, ensure_ascii=False, default=str), flush=True)


def adapter(run):
    return STATE / "runs" / run / "adapter"
