"""Short, isolated hardware trials using the same real GRPO and frozen-judge code as the study."""

import os
from functools import partial
from time import monotonic

from .curriculum import curriculum_problems
from .design import BASE, REVISION, Run
from .depth_review import effective_bit, numbers
from .frozen_gpu import GPUFitError, device_memory, process_dedicated_memory, require_dedicated_memory
from .learning_review import execute_steps
from .online_solvers import device_costs, initial_policy_digest, judge_session, score_chain
from .records import parse, solver_truth
from .storage import ORIGINAL_RESULTS, append, read_json, rows, stamp, write_json


BASE_ONLY = ("Qwen/Qwen3.5-2B-Base", "b1485b2fa6dfa1287294f269f5fb618e03d52d7c")
CANDIDATES = {"original-nf4":(BASE, REVISION, "nf4"), "original-bf16":(BASE, REVISION, "bf16"),
              "original-int8":(BASE, REVISION, "int8"), "base-2b":(*BASE_ONLY, "nf4")}


def starting_scores(pool, answers):
    """Re-execute each saved answer on the ordered calibration prefix, including interrupted probes."""
    data = list(answers)
    parsed = correct = 0
    for problem, row in zip(pool[:len(data)], data, strict=True):
        truth = execute_steps(problem)
        values = numbers(row["answer"], len(truth))
        observed = (problem.key, problem.expression, values is not None, values == truth)
        if observed != (row["key"], row["expression"], row["parsed"], row["correct"]):
            raise ValueError(f"Incorrect calibration order, parse or grade for {row['key']}")
        parsed += values is not None
        correct += values == truth
    return dict(n=len(data), correct=correct, parsed=parsed)


def memory_check(model, server):
    """Measure live physical allocations for both processes alongside actual parameter storage."""
    import torch
    storages = {t.untyped_storage().data_ptr():t.untyped_storage().nbytes() for t in (*model.parameters(),*model.buffers())}
    memory = dict(solver_state_mib=sum(storages.values())/2**20, solver_allocated_mib=torch.cuda.memory_allocated()/2**20,
                  solver_peak_mib=torch.cuda.max_memory_allocated()/2**20, gpu=device_memory())
    if os.name == "nt":
        memory["solver_dedicated_mib"] = process_dedicated_memory(os.getpid())
        memory["judge_dedicated_mib"] = process_dedicated_memory(server.process.pid)
        require_dedicated_memory(server.placement, memory["judge_dedicated_mib"])
        require_dedicated_memory(dict(weights_mib=memory["solver_state_mib"], cache_mib=0),memory["solver_dedicated_mib"])
    return memory


def probe(key):
    import torch
    from .backend import Backend
    from .training import train

    model_id, revision, precision = CANDIDATES[key]
    name = "solver-fit/"+key
    folder = ORIGINAL_RESULTS/name
    if (folder/"result.json").is_file():
        return read_json(folder/"result.json")
    profile = read_json(ORIGINAL_RESULTS/"calibrated/profile.json")
    spec = Run(name, family=profile["family"], prompt_style=profile["style"], reward="d3")
    pool = curriculum_problems(spec.family,"train",272)[256:272]
    # These are fresh solver weights before this disposable step. The check never opens a test split.
    receipt = dict(model=model_id, revision=revision, precision=precision, start=stamp(), device_before=device_memory())
    started = monotonic()
    try:
        with judge_session(name, "train") as runner:
            kept = []
            def policy(*args):
                torch.cuda.reset_peak_memory_stats()
                b = Backend(*args, model_id=model_id, revision=revision, precision=precision, text_only=model_id==BASE_ONLY[0])
                kept.append(b)
                initial_policy_digest(b.model)
                receipt["before_forward"] = memory_check(b.model, runner.backend)
                b.prompt_style = spec.prompt_style
                known = {r["key"] for r in rows(folder/"starting-answers.jsonl")}
                for pos in range(0,len(pool),4):
                    problems = pool[pos:pos+4]
                    if all(p.key in known for p in problems):
                        continue
                    answers = b.generate([b.prompt("solver",p) for p in problems], None,"fit_starting_solver", 911, False)
                    for p,answer in zip(problems,answers,strict=True):
                        if p.key not in known:
                            append(folder/"starting-answers.jsonl",dict(key=p.key,expression=p.expression,answer=answer,
                                   correct=solver_truth(p,answer)[0],parsed=parse(answer,len(p.values)) is not None, time=stamp()))
                return b

            effective = train(spec,1,partial(score_chain,runner.ask),backend_factory=policy)
            if kept:
                receipt["after_step"] = memory_check(kept[0].model,runner.backend)
                write_json(folder/"step-memory.json",receipt["after_step"])
            elif (folder/"step-memory.json").is_file():
                receipt["after_step"] = read_json(folder/"step-memory.json")
            else:
                raise ValueError("An interrupted probe has no post-update residency reading")
            samples = list(rows(folder/"rollouts.jsonl"))
            metrics = [r for r in rows(folder/"metrics.jsonl") if r.get("step")==1 and "grad_norm" in r]
            rewards = [s["reward"] for s in samples]
            if (effective["updates"]!=1 or len(samples)!=4 or len(metrics)!=1
                or any(len(s["reports"])!=3 or effective_bit(s["reports"][-1])!=s["reward"] for s in samples)
                or metrics[0]["rewards/registered_reward/mean"]!=sum(rewards)/4):
                raise ValueError("Incomplete real GRPO hardware trial")
            receipt.update(status="One update completed", updates=1, group_rewards=rewards,
                           gradient_norm=metrics[0]["grad_norm"], solver_usage=effective["usage"])
        receipt["judge_cost"] = device_costs(name,"train")
    except (GPUFitError, torch.cuda.OutOfMemoryError) as error:
        receipt.update(status="GPU fit unavailable",reason=str(error))
    receipt.update(starting_scores(pool, rows(folder/"starting-answers.jsonl")))
    if receipt["status"]=="One update completed" and receipt["n"]!=len(pool):
        raise ValueError("Incomplete starting-solver calibration cohort")
    receipt.update(time=stamp(), elapsed_seconds=monotonic()-started)
    write_json(folder/"result.json",receipt)
    return receipt


def fit_candidates(publish):
    """Probe the registered original precisions serially, then the documented pretraining-only candidate."""
    from .cli import study_lock,worker
    with study_lock("solver-precision"):
        def stage(key):
            folder=ORIGINAL_RESULTS/"solver-fit"/key
            if not (folder/"result.json").is_file():
                worker("solver-fit","--candidate",key)
            if publish:
                worker("publish","--milestone","solver-fit-"+key,"--run","solver-fit/"+key)
            return read_json(folder/"result.json")
        stage("original-nf4")
        if stage("original-bf16")["status"]=="GPU fit unavailable":
            stage("original-int8")
        stage("base-2b")
        if not publish:
            worker("report")
