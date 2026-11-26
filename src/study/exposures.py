"""Verify matched problem order and judge supervision examples from what the trainer observed."""

import hashlib
import json

from .storage import read_json, rows


def check_exposures(directory, runs):
    """Interventions sharing a seed and corpus must expose the same prompts in the same order."""
    groups, signatures = {}, {}
    for run in runs:
        target = directory / run.name
        updates = read_json(target / "trained.json")["updates"]
        digest = hashlib.sha256()
        observed, current = 0, None
        for index, row in enumerate(rows(target / "rollouts.jsonl")):
            step, sample = divmod(index, 4)
            if (row["step"], row["sample"], row["role"]) != (step, sample, run.role):
                raise RuntimeError(f"Unexpected GRPO group order in {run.name} at row {index}")
            entry = (row["key"], row["trace"], row["prior"])
            if sample == 0:
                current = entry
                digest.update((json.dumps(entry, separators=(",", ":"))+"\n").encode())
            elif entry != current:
                raise RuntimeError(f"Different prompts inside one GRPO group in {run.name} at update {step}")
            observed += 1
        if observed != 4*updates:
            raise RuntimeError(f"Incomplete training observations for {run.name}")
        signature = signatures[run.name] = digest.hexdigest()
        population = (run.seed, run.role, "arithmetic" if run.role == "solver" else run.corpus)
        if groups.setdefault(population, signature) != signature:
            raise RuntimeError(f"Unmatched training prompt order or preceding evidence in {run.name}")
    return signatures
