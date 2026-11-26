"""Evaluate natural outputs, independent voting, and visible or masked review-evidence twins."""

import hashlib

from .backend import Backend, stream_seed
from .design import matrix
from .domain import problems
from .judging import chain, majority, twin, votes
from .records import expected, mask_evidence, parse, solver_truth, sound, terminal
from .storage import RESULTS, Journal, adapter, append, read_json, rows, stamp, write_json


def weights_digest(name):
    weight = adapter(name) / "adapter_model.safetensors"
    with weight.open("rb") as file:
        return hashlib.file_digest(file, "sha256").hexdigest()


def seal():
    """Lock the entire model manifest before releasing any test labels or scores."""
    manifest = {}
    for run in matrix():
        if not (RESULTS / run.name / "development.json").is_file():
            raise RuntimeError(f"Development milestone pending for {run.name}")
        manifest[run.name] = weights_digest(run.name)
    path = RESULTS / "seal.json"
    previous = read_json(path)
    if previous and previous["weights"] != manifest:
        raise RuntimeError("The published test seal references different checkpoints")
    if not previous:
        write_json(path, {"time": stamp(), "weights": manifest})


def batches(split, n, path, size=8):
    """Skip fully persisted IDs and retain fixed batch membership and seed on restarts."""
    seen = {r["key"] for r in rows(path)}
    pool = problems(split, n)
    for pos in range(0, n, size):
        batch = pool[pos:pos+size]
        if any(p.key not in seen for p in batch):
            yield pos, batch, seen


def solutions(backend, run, snapshots, split, n, path, replay):
    policy = run.name if run and run.role == "solver" else None
    for pos, batch, seen in batches(split, n, path):
        seed = stream_seed("eval", split, pos)
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


def mechanisms(backend, snapshot, split, n, path, transfer=False):
    for pos, batch, seen in batches(split, n, path, size=4):
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


def evaluate(name, final=False):
    directory = RESULTS / name
    phase = "final" if final else "development"
    marker = directory / (phase+".json")
    if marker.is_file():
        return read_json(marker)
    run = next((r for r in matrix() if r.name == name), None)
    if not run and name != "base":
        raise ValueError(f"Unknown evaluation {name}")
    if final:
        frozen = read_json(RESULTS / "seal.json")
        if not frozen or (run and frozen["weights"].get(name) != weights_digest(name)):
            raise RuntimeError("Final evaluation requires the sealed checkpoint manifest")
    snapshots = list(run.judges if run else (None,)*3)
    if run and run.role.startswith("j"):
        snapshots[int(run.role[1:])-1] = run.name
    backend = Backend(Journal(name+"-"+phase), frozen=[*snapshots, name if run else None])
    if final:
        if not run or run.role == "solver":
            for split, count in (("test", 2048), ("layout", 128), ("long", 128)):
                solutions(backend, run, snapshots, split, count, directory/(split+".jsonl"), False)
        if not run or run.role == "j3" or name in ("exact-prefix3", "top-prefix3", "alt-exact-solver", "alt-top-solver"):
            mechanisms(backend, snapshots[2], "mechanism", 128, directory/"mechanism.jsonl")
            mechanisms(backend, snapshots[2], "layout", 128, directory/"transfer-evidence.jsonl", True)
        if run and run.role.startswith("j"):
            solutions(backend, run, snapshots, "test", 128, directory/"judge-test.jsonl", True)
    else:
        solutions(backend, run, snapshots, "dev", 32, directory/"replay.jsonl", True)
        if not run or run.role == "j3" or run.role == "solver":
            mechanisms(backend, snapshots[2], "dev", 8, directory/"development-twins.jsonl")
    result = {"time": stamp(), "phase": phase, "weights": weights_digest(name) if run else "frozen base",
              "usage": backend.totals}
    write_json(marker, result)
    return result
