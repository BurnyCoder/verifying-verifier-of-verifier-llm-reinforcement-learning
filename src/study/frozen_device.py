"""Verify and publish llama.cpp's actual GPU graph assignments from the experiment's native logs."""

import hashlib
import re
from collections import Counter

from .storage import ORIGINAL_RESULTS, log_directory, read_json, write_json


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
        if (folder/"gpu-graphs.json").is_file() or not read_json(marker).get("metrics"):
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
