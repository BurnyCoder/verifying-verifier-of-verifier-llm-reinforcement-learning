"""Reward fresh Qwen2.5 solvers with the independently confirmed frozen GGUF deployment."""

import hashlib
from contextlib import contextmanager
from functools import partial

from .benchmark import population
from .design import Run
from .domain import Problem
from .frozen_cases import CaseRunner
from .frozen_device import graph_assignments, measured_engine_times
from .frozen_gpu import BUILD, CONTEXT, LIMIT, LocalCUDA, weight_file
from .frozen_models import MODELS
from .storage import ORIGINAL_RESULTS, STATE, TRACK, Journal, adapter, log_directory, read_json, rows, stamp, write_json


ORIGINAL_PAIR = ("new-judges/winner-d2", "new-judges/winner-d3")
SINGLE = "new-judges/winner-d1"
NAMES = (SINGLE, *ORIGINAL_PAIR)


def selected_judge(root):
    """Bind the online reward to the exact model and decoder that passed independent confirmation."""
    decision = read_json(root/"decision.json", {})
    if decision.get("online_gate") is not True:
        raise ValueError("The frozen-judge confirmation gate has not passed")
    model = next(m for m in MODELS if m.key == decision["selected"])
    config = read_json(root/"confirm-winner/configuration.json", {})
    required = dict(model=model.title, repository=model.repository, revision=model.revision, file=model.filename,
                    sha256=model.sha256, base_revision=model.base_revision, build=BUILD, context=CONTEXT,
                    output_limit=LIMIT, placement="CUDA0", decoder="greedy, thinking disabled, raw generated tokens")
    if any(config.get(k) != v for k,v in required.items()):
        raise ValueError("Online judge configuration differs from the confirmed frozen deployment")
    return model


def recipe(name):
    """Use the original pair's settings for the registered single-judge extension."""
    if name not in NAMES or TRACK != "original":
        raise ValueError("Use the original results root for the newer-judge solver arms")
    if name == SINGLE:
        amendment = read_json(ORIGINAL_RESULTS/"new-judges/one-judge-plan.json", {})
        if amendment.get("parent") != "online-plan.json" or amendment.get("depth") != 1:
            raise ValueError("The single-judge arm requires the matched protocol addendum")
    plan = read_json(ORIGINAL_RESULTS/"new-judges/online-plan.json")
    profile = read_json(ORIGINAL_RESULTS/"calibrated/profile.json")
    if not plan or not profile or profile["updates"] != plan["updates"]:
        raise ValueError("The online plan and the calibrated budget must agree")
    return Run(name, seed=plan["seed"], reward=name[-2:], family=profile["family"], prompt_style=profile["style"])


def initial_policy_digest(model):
    """Prove equal starting adapters and check CUDA placement before the solver's first forward pass."""
    from peft import get_peft_model_state_dict
    import torch
    if any(t.device.type != "cuda" for t in (*model.parameters(), *model.buffers())):
        raise RuntimeError("The solver requires all model parameters and buffers on CUDA")
    digest = hashlib.sha256()
    for name, tensor in sorted(get_peft_model_state_dict(model).items()):
        digest.update(name.encode())
        digest.update(tensor.detach().contiguous().view(torch.uint8).cpu().numpy().tobytes())
    return digest.hexdigest()


def score_chain(ask, problems, traces, depth, step):
    """Score each live rollout. Only earlier reports for that same rollout enter the next prompt."""
    histories = [[] for _ in traces]
    for level in range(1, depth+1):
        for sample, (problem, trace, history) in enumerate(zip(problems, traces, histories, strict=True)):
            output = ask(f"{step}/{sample}/j{level}", level, problem, trace, history)
            history.append(output)
    return histories


@contextmanager
def judge_session(name, phase):
    """Use a separate read-only CUDA process. Preserve the costs and prompts of interrupted attempts."""
    folder = ORIGINAL_RESULTS/name
    model = selected_judge(ORIGINAL_RESULTS/"new-judges")
    config = read_json(ORIGINAL_RESULTS/"new-judges/confirm-winner/configuration.json")
    if read_json(folder/"configuration.json", config) != config:
        raise ValueError("Saved reward model changed")
    write_json(folder/"configuration.json", config)
    path = weight_file(model)
    attempt = stamp().replace(":", "-")
    directory = folder/phase/attempt
    directory.mkdir(parents=True, exist_ok=True)
    journal = Journal(name if phase=="train" else name+"-development")
    native = journal.path.with_name(attempt+"-server.log")
    with LocalCUDA(path, native, telemetry=directory/"gpu-telemetry.jsonl") as server:
        write_json(directory/"placement.json", server.placement)
        runner = CaseRunner(directory, server, model.sha256+"|"+BUILD+"|raw-v2|"+phase,
                            lambda event, **fields: journal.event("judge_"+event, **fields))
        yield runner
    write_json(directory/"graphs.json", graph_assignments(native))


def device_costs(name, phase):
    """Keep actual CUDA engine time, server timings, and solver CUDA-event time distinguishable."""
    attempts = sorted((ORIGINAL_RESULTS/name/phase).glob("*/placement.json"))
    calls = [r for p in attempts for r in rows(p.parent/"calls.jsonl")]
    graphs = []
    for placement in attempts:
        audit = placement.with_name("graphs.json")
        if not audit.is_file():
            native = log_directory()/(name if phase=="train" else name+"-development")/(placement.parent.name+"-server.log")
            write_json(audit, graph_assignments(native))
        graphs.append(read_json(audit))
    samples = [r for p in attempts for r in rows(p.parent/"gpu-telemetry.jsonl")]
    return dict(calls=len(calls), **{k:sum(r[k] for r in calls) for k in ("input_tokens","output_tokens","elapsed_seconds")},
                prompt_ms=sum(r["timings"]["prompt_ms"] for r in calls),
                generation_ms=sum(r["timings"]["predicted_ms"] for r in calls),
                gpu_engines=measured_engine_times(samples), graphs=graphs)


def train_online(name):
    from .training import train
    spec = recipe(name)
    folder = ORIGINAL_RESULTS/name
    if not (folder/"trained.json").is_file() or not (adapter(name)/"adapter_model.safetensors").is_file():
        with judge_session(name, "train") as runner:
            train(spec, read_json(ORIGINAL_RESULTS/"new-judges/online-plan.json")["updates"], partial(score_chain, runner.ask))
    write_json(folder/"train-cost.json", device_costs(name, "train"))


def evaluate_online(name):
    """Generate once from the trained policy, grade with integers, then audit the same literal answers."""
    import gc
    import torch
    from .backend import Backend
    from .evaluate import solutions, weights_digest
    from .online_report import exact_scores

    spec = recipe(name)
    folder = ORIGINAL_RESULTS/name
    weights = weights_digest(name)
    if (folder/"development.json").is_file():
        if read_json(folder/"development.json")["weights"] != weights:
            raise ValueError("Evaluated solver adapter changed")
        return
    if not (folder/"train-cost.json").is_file():
        raise ValueError("Finish the training milestone before scoring this solver")
    profile = read_json(ORIGINAL_RESULTS/"calibrated/profile.json")
    pool = population(profile, "dev", 32)
    keys = [p.key for p in pool]
    exact_scores(ORIGINAL_RESULTS/"calibrated/base/replay.jsonl", keys)
    previous = read_json(folder/"evaluation-input.json", {"weights":weights, "keys":keys})
    if previous != {"weights":weights, "keys":keys}:
        raise ValueError("Cannot reuse responses from different checkpoints or development IDs")
    write_json(folder/"evaluation-input.json", previous)
    backend = Backend(Journal(name+"-development"), frozen=[name], seed=spec.seed)
    backend.prompt_style = spec.prompt_style
    initial_policy_digest(backend.model)
    solutions(backend, spec, (), "dev", len(pool), folder/"solutions.jsonl", False, pool=pool)
    exact = exact_scores(folder/"solutions.jsonl", keys)
    del backend
    gc.collect()
    torch.cuda.empty_cache()
    with judge_session(name, "development") as runner:
        for row in rows(folder/"solutions.jsonl"):
            runner.chain("natural", Problem.from_expression(row["expression"]), row["trace"])
        cases = list(runner.completed.values())
        if len(cases) != len(keys) or any(row["valid"] != exact[row["key"]] for row in cases):
            raise ValueError("Incomplete fixed-answer development replay")
        write_json(folder/"replay-audit.json", cases)
    write_json(folder/"development.json", dict(time=stamp(), weights=weights, correct=sum(exact.values()), n=len(exact),
               judge_cost=device_costs(name, "development")))


def campaign(publish=False):
    """Finish the original pair, then its registered extension, with resumable milestone publication."""
    from .cli import study_lock, worker
    with study_lock("online-solvers"):
        root = ORIGINAL_RESULTS/"new-judges"
        selected_judge(root)
        single = (root/"one-judge-plan.json").is_file()
        for name in (*ORIGINAL_PAIR, SINGLE) if single else ORIGINAL_PAIR:
            recipe(name)
            for action, marker, phase in (("train","train-cost","trained"),("evaluate","development","development")):
                if not (ORIGINAL_RESULTS/name/(marker+".json")).is_file():
                    worker(action, "--run", name)
                milestone = name.replace("/", "-")+"-"+phase
                if publish and not (STATE/"publication"/(milestone+".json")).is_file():
                    worker("publish", "--milestone", milestone, "--run", name)
                elif not publish:
                    worker("report")
        milestone = "new-judges-three-depth-comparison" if single else "new-judges-online-comparison"
        if publish:
            worker("publish","--milestone",milestone)
        else:
            worker("report")
