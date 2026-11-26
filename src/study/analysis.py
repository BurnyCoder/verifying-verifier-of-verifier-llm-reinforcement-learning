"""Paired inference over independent problem IDs, conditional on the trained checkpoints."""

import numpy as np

from .design import SEEDS


def paired_primary(outcomes, required_n=2048):
    keys, differences, per_seed = None, [], {}
    for seed in SEEDS:
        deep, shallow = (outcomes.get(f"{arm}-{seed}", {}) for arm in ("d3", "d2"))
        if len(deep) != required_n or deep.keys() != shallow.keys():
            return {"status": "pending", "reason": "Incomplete matched final checkpoints or IDs", "per_seed": per_seed}
        if keys is None:
            keys = sorted(deep)
        if set(keys) != set(deep):
            return {"status": "pending", "reason": "Different problem IDs across seeds", "per_seed": per_seed}
        values = np.asarray([deep[k] - shallow[k] for k in keys], dtype=float)
        differences.append(values)
        per_seed[str(seed)] = float(values.mean())
    paired = np.mean(differences, axis=0)
    rng = np.random.default_rng(20261126)
    # Chunk resampling bounds memory while retaining the same seeds and arms for every ID.
    bootstrap = np.concatenate([paired[rng.integers(len(paired), size=(100, len(paired)))].mean(axis=1)
                                for _ in range(100)])
    lo, hi = np.quantile(bootstrap, [0.025, 0.975])
    status = "supports target" if lo > 0.03 else "rules out target" if hi < 0.03 else "inconclusive"
    return {"status": status, "n": required_n, "delta": float(paired.mean()), "ci": [float(lo), float(hi)],
            "per_seed": per_seed, "interval_unit": "problem, conditional on the three matched seeds"}
