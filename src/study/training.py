"""Online GRPO using TRL's policy update and an independently logged reward function."""

import hashlib
import json
import math
import random
import time
from dataclasses import asdict

import torch
from datasets import Dataset
from transformers import TrainerCallback
from trl import GRPOConfig, GRPOTrainer

from .backend import Backend, stream_seed
from .checkpoints import last_complete
from .curriculum import curriculum_problems
from .design import matrix, permute_groups
from .domain import Problem, problems
from .judging import chain, make_example, majority, votes
from .records import approval, expected, solver_truth, sound, terminal
from .storage import RESULTS, STATE, Journal, adapter, append, generation_cost, read_json, retain, rows, stamp, write_json


def frozen_sources(run):
    sources = [*run.judges, run.teacher]
    if run.corpus != "base":
        origin = next(row for row in matrix() if row.name == run.corpus)
        sources.extend((origin.name, *origin.judges))
    return sources


def corpus(backend, run, pool):
    """Cache the same unaltered training traces for both judge-supervision routes."""
    path = RESULTS / "corpora" / (run.corpus+".jsonl")
    saved = {r["key"]: r for r in rows(path)}
    origin = next((r for r in matrix() if r.name == run.corpus), None)
    needed = [p for i, p in enumerate(pool) if i % 4 == 0]
    for offset in range(0, len(needed), 4):
        batch = needed[offset:offset+4]
        if all(p.key in saved for p in batch):
            continue
        seed = stream_seed("corpus", run.corpus, batch[0].key)
        traces = backend.generate([backend.prompt("solver", p) for p in batch], origin.name if origin else None,
                                  "corpus_solver", seed, True)
        histories = chain(backend, batch, traces, origin.judges if origin else (None,)*3, 2, seed)
        for p, t, h in zip(batch, traces, histories, strict=True):
            if p.key in saved:
                continue
            entry = {"key": p.key, "expression": p.expression, "trace": t, "reports": h}
            append(path, entry)
            saved[p.key] = entry
    return saved


def training_data(backend, run, count):
    pool = curriculum_problems(run.family,"train",max(32,count)) if run.family else problems("train", max(32, count))
    natural = corpus(backend, run, pool) if run.role != "solver" else {}
    records = []
    for i, p in enumerate(pool):
        trace, history = ("", []) if run.role == "solver" else make_example(p, run.role, i, natural.get(p.key))
        records.append(dict(prompt=backend.prompt(run.role, p, trace, history), expression=p.expression,
                            trace=trace, history_json=json.dumps(history)))
    return Dataset.from_list(records)


class Reward:
    """Supply only the assigned training signal while separately writing oracle observations."""

    def __init__(self, backend, run, external_chain=None):
        self.backend, self.run = backend, run
        self.external_chain = external_chain
        self.__name__ = "registered_reward"

    def __call__(self, prompts, completions, expression, trace, history_json, trainer_state, **kwargs):
        run = self.run
        step = trainer_state.global_step
        dataset = [Problem.from_expression(e) for e in expression]
        incoming = [json.loads(h) for h in history_json]
        seed = stream_seed("reward", run.seed, step)
        histories = [[] for _ in dataset]
        if run.role == "solver":
            truth = [solver_truth(p, answer) for p, answer in zip(dataset, completions, strict=True)]
            labels = [r[0] for r in truth]
            if run.reward in ("oracle","oracle-shuffle"):
                rewards = labels.copy()
                if run.reward=="oracle-shuffle":
                    rewards = permute_groups(rewards,random.Random(seed))
            elif run.reward == "flat":
                histories = votes(self.backend, dataset, completions, seed, run.judges)
                rewards = [majority(h) for h in histories]
            else:
                depth = {"d1": 1, "d2": 2}.get(run.reward, 3)
                histories = (self.external_chain(dataset, completions, depth, step) if self.external_chain
                             else chain(self.backend, dataset, completions, run.judges, depth, seed))
                rewards = [terminal(h[-1], depth) for h in histories]
                if run.reward == "hybrid":
                    rewards = [j*o for j, o in zip(rewards, labels, strict=True)]
                if run.reward == "shuffle":
                    rewards = permute_groups(rewards, random.Random(seed))
        else:
            truth = [expected(p, t, h) for p, t, h in zip(dataset, trace, incoming, strict=True)]
            labels = [int(sound(answer, ref)) for answer, ref in zip(completions, truth, strict=True)]
            if run.reward == "exact":
                rewards = labels.copy()
            else:
                higher = f"j{int(run.role[1:])+1}"
                requests = [self.backend.prompt(higher, p, t, [*h, a])
                            for p, t, h, a in zip(dataset, trace, incoming, completions, strict=True)]
                audits = self.backend.generate(requests, run.teacher, higher, seed, True)
                histories = [[a] for a in audits]
                rewards = [approval(a) for a in audits]
        for i, p in enumerate(dataset):
            append(RESULTS / run.name / "rollouts.jsonl",
                   dict(step=step, sample=i, key=p.key, expression=p.expression, role=run.role, answer=completions[i],
                        trace=trace[i], prior=incoming[i], reports=histories[i], label=labels[i],
                        expected=truth[i], reward=rewards[i], time=stamp()))
        self.backend.journal.event("reward", step=step, rewards=rewards, exact=labels,
                                   zero_variance=len(set(rewards)) == 1)
        return rewards


def frozen_fingerprint(model):
    """Checksum every loaded reward adapter and assert the optimizer can update only the policy."""
    digest = hashlib.sha256()
    for name, value in model.named_parameters():
        if value.requires_grad and ".default." not in name:
            raise RuntimeError(f"Unexpected trainable parameter {name}")
        if ".snapshot_" in name:
            digest.update(name.encode())
            digest.update(value.detach().cpu().contiguous().view(torch.uint8).numpy().tobytes())
    return digest.hexdigest()


class Metrics(TrainerCallback):
    def __init__(self, backend, run, steps, prior_seconds=0):
        self.backend, self.run, self.steps = backend, run, steps
        self.started = None
        self.prior_seconds = prior_seconds

    def on_train_begin(self, args, state, control, **kwargs):
        self.started = time.monotonic()

    def on_log(self, args, state, control, logs=None, **kwargs):
        if logs:
            values = {k: (v if math.isfinite(v) else None) for k, v in logs.items() if isinstance(v, (int, float))}
            append(RESULTS / self.run.name / "metrics.jsonl", dict(step=state.global_step, time=stamp(), **values))

    def on_step_end(self, args, state, control, **kwargs):
        append(RESULTS / self.run.name / "cost.jsonl",dict(step=state.global_step,usage=self.backend.totals,
               elapsed_seconds=self.prior_seconds+time.monotonic()-self.started))
        if self.run.name == "timing" or state.global_step % 32 or self.run.role != "solver":
            return
        batch = curriculum_problems(self.run.family,"confirm",8) if self.run.family else problems("dev", 8)
        answers = self.backend.generate([self.backend.prompt("solver", p) for p in batch], "@active",
                                        "development_solver", 911, False)
        correct = sum(solver_truth(p, t)[0] for p, t in zip(batch, answers, strict=True))
        append(RESULTS / self.run.name / "metrics.jsonl", dict(step=state.global_step, time=stamp(),
               development_accuracy=correct/len(batch), development_n=len(batch)))


def record_timing_budget(result):
    seconds = result["elapsed_seconds"] / result["updates"]
    count = max((n for n in (16,32,64,128,256) if 32*n*seconds <= 0.6*7*86400 and n*seconds <= 12*3600), default=16)
    write_json(RESULTS / "budget.json", dict(updates=count, seconds_per_update=seconds, time=stamp()))


def train(run, steps, external_chain=None):
    out = RESULTS / run.name
    finished = read_json(out / "trained.json")
    if finished and (adapter(run.name) / "adapter_config.json").is_file():
        if run.name == "timing" and not (RESULTS / "budget.json").is_file():
            record_timing_budget(finished)
        return finished
    journal = Journal(run.name)
    backend = Backend(journal, run.initial, frozen_sources(run), run.seed)
    backend.label = run.role
    backend.prompt_style = run.prompt_style
    identity = {}
    if external_chain is not None:
        from .online_solvers import initial_policy_digest
        identity["initial_adapter_sha256"] = initial_policy_digest(backend.model)
    data = training_data(backend, run, steps)
    work = STATE / "runs" / run.name / "trainer"
    work.mkdir(parents=True, exist_ok=True)
    checkpoint, last_step = last_complete(work)
    resume = str(checkpoint) if checkpoint else None
    retain(out / "rollouts.jsonl", lambda row: row["step"] < last_step)
    retain(out / "metrics.jsonl", lambda row: row["step"] <= last_step)
    retain(out / "cost.jsonl", lambda row: row["step"] <= last_step)
    latest_cost=next(reversed(list(rows(out/"cost.jsonl"))),{})
    for role, counts in latest_cost.get("usage",{}).items():
        existing=backend.totals.setdefault(role,{})
        for key,value in counts.items():
            existing[key]=existing.get(key,0)+value
    args = GRPOConfig(output_dir=str(work), max_steps=steps, per_device_train_batch_size=1,
                      gradient_accumulation_steps=4, num_generations=4, num_iterations=1, loss_type="grpo",
                      beta=0.0, epsilon=0.2, scale_rewards="group", learning_rate=3e-5, lr_scheduler_type="constant",
                      max_completion_length=48, temperature=0.8, top_p=1.0, top_k=0, bf16=True,
                      seed=run.seed, data_seed=run.seed, gradient_checkpointing=True,
                      gradient_checkpointing_kwargs={"use_reentrant": False}, optim="adamw_torch",
                      save_strategy="steps", save_steps=min(8, steps), save_total_limit=2, logging_steps=1,
                      report_to="none", disable_tqdm=True, remove_unused_columns=False, dataloader_num_workers=0)
    monitor = Metrics(backend, run, steps,latest_cost.get("elapsed_seconds",0))
    trainer = GRPOTrainer(model=backend.model, args=args, processing_class=backend.tokenizer, train_dataset=data,
                          reward_funcs=Reward(backend, run, external_chain), callbacks=[monitor])
    before = frozen_fingerprint(backend.model)
    recipe = {"run": asdict(run), "updates": steps, "group": 4, **identity}
    previous = read_json(out/"recipe.json", {})
    if external_chain and previous and any(previous.get(k)!=v for k,v in json.loads(json.dumps(recipe)).items()):
        raise ValueError("Online solver initialization or optimizer recipe changed on resume")
    write_json(out / "recipe.json", {**recipe, "started": previous.get("started") or stamp()})
    journal.event("training_start", resume=resume, updates=steps, completed=last_step)
    trainer.train(resume_from_checkpoint=resume)
    elapsed = monitor.prior_seconds+time.monotonic()-monitor.started
    after = frozen_fingerprint(backend.model)
    if before != after:
        raise RuntimeError("Frozen judge adapter changed during optimization")
    backend.model.save_pretrained(adapter(run.name), selected_adapters=["default"])
    result = dict(time=stamp(), run=asdict(run), updates=trainer.state.global_step,
                  elapsed_seconds=elapsed, resumed_at=last_step, frozen_checksum=after, **identity, **generation_cost(run.name,backend.totals))
    if run.name == "timing":
        record_timing_budget(result)
    write_json(out / "trained.json", result)
    return result
