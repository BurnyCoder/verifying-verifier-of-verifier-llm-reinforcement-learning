"""Verify and publish llama.cpp's actual GPU graph assignments from the experiment's native logs."""

import hashlib
import re
from collections import Counter
from datetime import datetime
from itertools import pairwise

from .storage import ORIGINAL_RESULTS, log_directory, read_json, write_json


def measured_engine_times(samples):
    """Sum physical adjacent WDDM counter differences within one server and GPU engine."""
    # Microsoft defines active time as the difference between samples of a timer counter.
    # https://learn.microsoft.com/en-us/windows/win32/wmisdk/timer-algorithm-counter-types
    totals = {}
    for before, after in pairwise(samples):
        if (before['pid'], before.get('process_start')) != (after['pid'], after.get('process_start')):
            continue
        wall = (datetime.fromisoformat(after['time'])-datetime.fromisoformat(before['time'])).total_seconds()
        old = {e.get('instance',e['engine']):e for e in before['engines']}
        old_counts = Counter(e.get('instance',e['engine']) for e in before['engines'])
        new_counts = Counter(e.get('instance',e['engine']) for e in after['engines'])
        for reading in after['engines']:
            identity = reading.get('instance',reading['engine'])
            if identity not in old:
                continue
            previous = old[identity]
            total = totals.setdefault(reading['engine'],dict(engine=reading['engine'],seconds=0.,interval_seconds=0.,usable=0,discarded=0))
            elapsed, active = wall, reading['seconds']-previous['seconds']
            if 'running_ticks' in reading and 'running_ticks' in previous:
                frequency = reading['frequency']
                elapsed = (int(reading['sample_ticks'])-int(previous['sample_ticks']))/frequency
                active = (int(reading['running_ticks'])-int(previous['running_ticks']))/frequency
            if old_counts[identity]!=1 or new_counts[identity]!=1 or elapsed<=0 or not 0<=active<=elapsed:
                total['discarded']+=1
                continue
            total['seconds']+=active
            total['interval_seconds']+=elapsed
            total['usable']+=1
    return list(totals.values())


def graph_assignments(path):
    """CUDA0 is the only permitted compute graph backend. CPU tokenization is outside these graphs."""
    digest, counts = hashlib.sha256(), Counter()
    pattern = re.compile(rb"## SPLIT #\d+: (\S+) # \d+ inputs")
    with path.open("rb") as source:
        for line in source:
            digest.update(line)
            for name in pattern.findall(line):
                counts[name.decode("ascii")]+=1
    if not counts or set(counts)!={"CUDA0"}:
        raise ValueError(f"Unverified CPU-free computation in {path.name}: {dict(counts)}")
    return dict(log=path.name,sha256=digest.hexdigest(),graph_assignments=dict(counts))


def close_device_records():
    """Attach the logs for each scored load to its raw receipt. Skip archived/pre-fix pilot calls."""
    for marker in (ORIGINAL_RESULTS/"new-judges").glob("*/result.json"):
        folder = marker.parent
        receipt = read_json(marker)
        if (folder/"gpu-graphs.json").is_file() or not (receipt.get("metrics") or receipt.get("latency")):
            continue
        logs = sorted((log_directory()/("new-judges-"+folder.name)).glob("*-server.log"))
        if not logs:
            continue
        # A fit event is timestamped after the server is ready. Select its immediately preceding native log.
        used = set()
        for fit in read_json(folder/"fit.json",[]):
            if fit["fit"]:
                upper = fit["time"].replace(":","-")
                earlier = [p for p in logs if p.name.removesuffix("-server.log")<=upper]
                if not earlier:
                    raise ValueError("Missing server log for a verified GPU placement")
                used.add(earlier[-1])
        if used:
            write_json(folder/"gpu-graphs.json",{"loads":[graph_assignments(p) for p in sorted(used)]})
