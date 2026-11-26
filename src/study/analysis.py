"""Paired inference over independent problem IDs, conditional on the trained checkpoints."""

import numpy as np

from .design import SEEDS
from .records import parse


def paired_comparison(outcomes, reference, required_n=2048):
    """Use a shared bootstrap index for every checkpoint, as in scipy.stats.bootstrap(paired=True)."""
    keys, differences, per_seed = None, [], {}
    for seed in SEEDS:
        deep, shallow = (outcomes.get(f"{arm}-{seed}", {}) for arm in ("d3", reference))
        if len(deep) != required_n or deep.keys() != shallow.keys():
            return {"status": "pending", "reason": "Incomplete matched final checkpoints or IDs", "per_seed": per_seed}
        if keys is None:
            keys = sorted(deep)
        if set(keys) != set(deep):
            return {"status": "pending", "reason": "Different problem IDs across seeds", "per_seed": per_seed}
        values = np.asarray([deep[k] - shallow[k] for k in keys], dtype=float)
        differences.append(values)
        per_seed[str(seed)] = float(values.mean())
    contrasts = np.column_stack(differences)
    paired = np.column_stack((contrasts.mean(axis=1), contrasts))
    rng = np.random.default_rng(20261126)
    # Each row is an independent problem. Keep the pooled statistic and every seed together.
    bootstrap = np.concatenate([paired[rng.integers(len(paired), size=(100, len(paired)))].mean(axis=1)
                                for _ in range(100)])
    intervals = np.quantile(bootstrap, [0.025, 0.975], axis=0).T.tolist()
    return {"status": "estimated", "n": required_n, "delta": float(paired[:, 0].mean()), "ci": intervals[0],
            "per_seed": per_seed, "seed_intervals": dict(zip(map(str, SEEDS), intervals[1:], strict=True)),
            "interval_unit": "problem, conditional on the trained checkpoints"}


def paired_primary(outcomes, required_n=2048):
    estimate = paired_comparison(outcomes, "d2", required_n)
    if "ci" in estimate:
        lo, hi = estimate["ci"]
        estimate["status"] = "supports target" if lo > .03 else "rules out target" if hi < .03 else "inconclusive"
    return estimate


def replay_metrics(sample):
    """Count false accepts among incorrect traces and false rejects among correct traces."""
    valid = sum(r["correct"] for r in sample)
    results = []
    for order, label in enumerate(("D1", "D2", "D3", "Flat")):
        pairs = [(r["verdicts"][order] if order < 3 else r["flat"], r["correct"]) for r in sample]
        malformed = (sum(r["judge_malformed"][order] for r in sample) if order < 3 else
                     sum(parse(v, 3) is None for r in sample for v in r["votes"]))
        results.append(dict(method=label, n=len(pairs), valid=valid, invalid=len(pairs)-valid,
                            agreement=sum(a == b for a,b in pairs)/len(pairs) if pairs else None,
                            evidence_correct=sum(r["full_report_correct"][order] for r in sample) if order<3 else None,
                            false_accept=sum(a == 1 and b == 0 for a,b in pairs),
                            false_reject=sum(a == 0 and b == 1 for a,b in pairs), malformed=malformed,
                            reports=len(pairs) if order < 3 else sum(len(r["votes"]) for r in sample)))
    return results


def evidence_fields(pairs, condition):
    """Distinguish a correct solution bit from identifying and repairing faulty review evidence."""
    counts = dict(reports=0, parsed=0, solution_bit=0, audit_bit=0, faults=0, localized_and_repaired=0)
    for pair in pairs:
        for answer, expected in zip(pair[condition], pair["labels"], strict=True):
            counts["reports"] += 1
            counts["faults"] += expected[0]==0
            observed = parse(answer, 6)
            if observed is not None:
                counts["parsed"] += 1
                counts["solution_bit"] += observed[3]==expected[3]
                counts["audit_bit"] += observed[0]==expected[0]
                counts["localized_and_repaired"] += expected[0]==0 and observed[:3]==tuple(expected[:3])
    return counts
