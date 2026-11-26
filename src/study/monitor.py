"""Check long-running workers at the study's requested cadence without running extra inference."""

import json
import subprocess
import time

from .storage import RESULTS, ROOT, append, atomic, read_json, rows, stamp


def cadence(expected_seconds):
    if expected_seconds > 3600:
        return 1800
    return 900 if expected_seconds > 1800 else 300


def inspect_worker(name, phase, elapsed):
    """Write one timestamped observation, including a throughput estimate when training has started."""
    target = RESULTS / name
    entry = dict(time=stamp(), run=name, phase=phase, elapsed_seconds=elapsed)
    estimated = elapsed
    if phase == "train":
        recipe = read_json(target/"recipe.json", {})
        cost = next(reversed(list(rows(target/"cost.jsonl"))), {})
        step, total = cost.get("step", 0), recipe.get("updates")
        entry.update(step=step, target_updates=total)
        if step and total:
            seconds_per_update = cost["elapsed_seconds"]/step
            estimated = seconds_per_update*total
            entry["remaining_seconds"] = max(total-step,0)*seconds_per_update
            message = (f"{step} of {total} optimizer updates completed. At the observed mean of "
                       f"{seconds_per_update:.1f} seconds per update, about {entry['remaining_seconds']/3600:.2f} hours remain.")
        else:
            message = "Model setup, corpus preparation or the first optimizer update is in progress."
    else:
        files = ("replay", "development-twins") if phase=="development" else (
            "test", "long", "layout", "judge-test", "mechanism", "unseen-evidence", "layout-evidence", "transfer-evidence")
        counts = {}
        for cohort in files:
            path = target/(cohort+".jsonl")
            if path.exists():
                # Count closed lines only. A partial sealed evaluation discloses no predictions or scores.
                with path.open("rb") as source:
                    counts[cohort] = sum(line.endswith(b"\n") for line in source)
        entry["records"] = counts
        message = "Completed records by cohort. "+", ".join(f"{key} {count}" for key,count in counts.items()) if counts else "Evaluation initialization is in progress."
    delay = entry["next_check_seconds"] = cadence(estimated)
    append(target/"monitor.jsonl",entry)
    progress = ROOT/"reports/progress.md"
    previous = progress.read_text(encoding="utf-8") if progress.is_file() else "# Study progress"
    body = previous.partition("<!-- CURRENT-WORKER -->")[0].rstrip()
    atomic(progress, f"{body}\n\n<!-- CURRENT-WORKER -->\n### Current worker\n\n{entry['time']} · {name} · {phase}. {message} The next scheduled check is in {delay//60} minutes.\n")
    print(json.dumps(entry), flush=True)
    return entry


def supervise(command, name, phase):
    """Wake immediately on worker exit and record periodic observations while it is alive."""
    budget = read_json(RESULTS/"budget.json", {})
    estimate = budget.get("seconds_per_update", 0)*budget.get("updates", 0) if name.startswith("d3-") and phase=="train" else 0
    delay = cadence(estimate)
    started = time.monotonic()
    with subprocess.Popen(command) as process:
        while True:
            try:
                status = process.wait(timeout=delay)
            except subprocess.TimeoutExpired:
                delay = inspect_worker(name, phase, time.monotonic()-started)["next_check_seconds"]
                continue
            if status:
                raise subprocess.CalledProcessError(status, command)
            return
