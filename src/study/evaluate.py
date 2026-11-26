"""Evaluate natural outputs, independent voting, and visible or masked review-evidence twins."""

import hashlib

from .backend import Backend, stream_seed
from .benchmark import active_profile, population
from .design import matrix
from .domain import problems
from .exposures import check_exposures
from .judging import chain, majority, twin, votes
from .records import expected, mask_evidence, parse, solver_truth, sound, terminal
from .storage import RESULTS, Journal, adapter, append, atomic, read_json, rows, stamp, write_json


def weights_digest(name):
    weight = adapter(name) / "adapter_model.safetensors"
    with weight.open("rb") as file:
        return hashlib.file_digest(file, "sha256").hexdigest()


def seal():
    """Lock the entire model manifest before releasing any test labels or scores."""
    manifest = {}
    for run in matrix():
        development = read_json(RESULTS / run.name / "development.json")
        if not development:
            raise RuntimeError(f"Development milestone pending for {run.name}")
        digest = weights_digest(run.name)
        if development["weights"] != digest:
            raise RuntimeError(f"Checkpoint changed after development evaluation for {run.name}")
        manifest[run.name] = digest
    path = RESULTS / "seal.json"
    previous = read_json(path)
    if previous and previous["weights"] != manifest:
        raise RuntimeError("The published test seal references different checkpoints")
    if not previous:
        exposures = check_exposures(RESULTS, matrix())
        write_json(path, {"time": stamp(), "weights": manifest, "ordered_training_exposures": exposures})


def batches(split, n, path, size=8, population=None):
    """Skip fully persisted IDs and retain fixed batch membership and seed on restarts."""
    seen = {r["key"] for r in rows(path)}
    pool = problems(split, n) if population is None else population
    for pos in range(0, n, size):
        batch = pool[pos:pos+size]
        if any(p.key not in seen for p in batch):
            yield pos, batch, seen


def solutions(backend, run, snapshots, split, n, path, replay, stored_traces=None, pool=None):
    policy = run.name if run and run.role == "solver" else None
    for pos, batch, seen in batches(split, n, path, population=pool):
        seed = stream_seed("eval", split, pos)
        if stored_traces is not None and all(p.key in stored_traces for p in batch):
            traces = [stored_traces[p.key] for p in batch]
        else:
            traces = backend.generate([backend.prompt("solver", p) for p in batch], policy, "eval_solver", seed, False)
        histories = chain(backend, batch, traces, snapshots, 3, seed) if replay else [[] for _ in batch]
        ballots = votes(backend, batch, traces, seed, snapshots) if replay else [[] for _ in batch]
        for p, t, h, v in zip(batch, traces, histories, ballots, strict=True):
            if p.key in seen:
                continue
            oracle = solver_truth(p, t)
            numbers = parse(t, len(p.values))
            entry = dict(key=p.key, expression=p.expression, problem=list(p.steps), trace=t, expected_values=p.values,
                         correct=oracle[0], final_correct=int(numbers is not None and numbers[-1] == p.values[-1]),
                         malformed=numbers is None, split=split, reports=h, votes=v)
            if replay:
                bits = [terminal(report, i) for i, report in enumerate(h, 1)]
                entry.update(verdicts=bits, flat=majority(v), full_report_correct=[
                    int(sound(report, expected(p, t, h[:i]))) for i, report in enumerate(h)],
                    judge_malformed=[parse(report, 3 if i == 0 else 6) is None for i, report in enumerate(h)],
                    fixed=int(bits[1] != oracle[0] and bits[2] == oracle[0]),
                    harmed=int(bits[1] == oracle[0] and bits[2] != oracle[0]))
            append(path, entry)


def mechanisms(backend, snapshot, split, n, path, transfer=False, population=None):
    for pos, batch, seen in batches(split, n, path, size=4,population=population):
        prepared, requests, masked_requests = [], [], []
        for index, p in enumerate(batch, pos):
            trace, first, good, bad = twin(p, index, transfer)
            reports = (bad, good) if index % 2 else (good, bad)
            for previous in reports:
                requests.append(backend.prompt("j3", p, trace, [first, previous]))
                masked_requests.append(backend.prompt("j3", p, trace, [first, mask_evidence(previous)]))
            prepared.append((p, trace, first, reports))
        seed = stream_seed("twins", split, pos)
        visible = backend.generate(requests, snapshot, "j3_visible", seed, False)
        masked = backend.generate(masked_requests, snapshot, "j3_masked", seed, False)
        for j, (p, t, first, reports) in enumerate(prepared):
            if p.key in seen:
                continue
            start = 2*j
            labels = [expected(p, t, [first, report]) for report in reports]
            va, ma = visible[start:start+2], masked[start:start+2]
            append(path, dict(key=p.key, expression=p.expression, trace=t, first=first, reviews=reports,
                              labels=labels, visible=va, masked=ma, split=split,
                              visible_pair=int(all(sound(a, b) for a,b in zip(va,labels,strict=True))),
                              masked_pair=int(all(sound(a, b) for a,b in zip(ma,labels,strict=True)))))


def evidence_cohort(backend, snapshot, name, phase, split, count, filename, transfer=False, pool=None):
    """Identical frozen J3, prompts and deterministic decoder yield one shared evidence measurement."""
    reference = snapshot or "base"
    target = RESULTS / name / filename
    source = RESULTS / reference / filename
    marker = read_json(RESULTS / reference / (phase+".json"))
    if name != reference and marker and source.is_file():
        expected_weight = weights_digest(snapshot) if snapshot else "frozen base"
        records = list(rows(source))
        if marker["weights"] == expected_weight and len({r["key"] for r in records}) == len(records) == count:
            atomic(target, source.read_text(encoding="utf-8"))
            backend.journal.event("shared_evidence_measurement", cohort=filename, source=reference, pairs=count)
            return reference
    mechanisms(backend, snapshot, split, count, target, transfer, pool)
    return name


def evaluate(name, final=False):
    directory = RESULTS / name
    phase = "final" if final else "development"
    marker = directory / (phase+".json")
    if marker.is_file():
        return read_json(marker)
    run = next((r for r in matrix() if r.name == name), None)
    if not run and name != "base":
        raise ValueError(f"Unknown evaluation {name}")
    snapshots = list(run.judges if run else (None,)*3)
    if run and run.role.startswith("j"):
        snapshots[int(run.role[1:])-1] = run.name
    if final:
        frozen = read_json(RESULTS / "seal.json")
        used = {s for s in snapshots if s}
        if run:
            used.add(name)
        if not frozen or any(frozen["weights"].get(s) != weights_digest(s) for s in used):
            raise RuntimeError("Final evaluation requires every participating checkpoint to match the seal")
    profile = active_profile()
    backend = Backend(Journal(name+"-"+phase), frozen=[*snapshots, name if run else None])
    backend.prompt_style = profile.get("style", "registered")
    evidence_sources = {}
    if final:
        if not run or run.role == "solver":
            suites = [("test", 2048), ("layout", 128), ("long", 128)]
            if profile and profile["family"] != "registered":
                suites.append(("original-difficulty", 2048))
            for split, count in suites:
                solutions(backend, run, snapshots, split, count, directory/(split+".jsonl"), False,
                          pool=population(profile, split, count))
        if not run or run.role == "j3" or name in ("exact-prefix3", "top-prefix3", "alt-exact-solver", "alt-top-solver"):
            cohorts = (("mechanism", "mechanism.jsonl", False), ("mechanism", "unseen-evidence.jsonl", True),
                       ("layout", "layout-evidence.jsonl", False), ("layout", "transfer-evidence.jsonl", True))
            for split, filename, transfer in cohorts:
                evidence_sources[filename] = evidence_cohort(backend, snapshots[2], name, phase, split, 128,
                                                             filename, transfer, population(profile, split, 128))
        if name in ("base", "d3-17") or run.role.startswith("j"):
            # Reuse the exact greedy outputs already observed on this fixed test prefix.
            origin = directory if name == "d3-17" else RESULTS / "base"
            stored = {r["key"]: r["trace"] for r in rows(origin / "test.jsonl")}
            solutions(backend, run, snapshots, "test", 128, directory/"judge-test.jsonl", True, stored,
                      population(profile, "test", 128))
    else:
        solutions(backend, run, snapshots, "dev", 32, directory/"replay.jsonl", True,
                  pool=population(profile, "dev", 32))
        if not run or run.role == "j3" or run.role == "solver":
            filename = "development-twins.jsonl"
            evidence_sources[filename] = evidence_cohort(backend, snapshots[2], name, phase, "dev", 8, filename,
                                                         pool=population(profile, "dev", 8))
    result = {"time": stamp(), "phase": phase, "weights": weights_digest(name) if run else "frozen base",
              "usage": backend.totals, "evidence_sources": evidence_sources, "profile": profile}
    write_json(marker, result)
    return result
