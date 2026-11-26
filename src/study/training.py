"""Online GRPO using TRL's policy update and an independently logged reward function."""

import hashlib
import json
import math
import random
import time
from dataclasses import asdict
from pathlib import Path

import torch
from datasets import Dataset
from transformers import TrainerCallback
from transformers.trainer_utils import get_last_checkpoint
from trl import GRPOConfig, GRPOTrainer

from .backend import Backend, stream_seed
from .design import matrix, permute_groups
from .domain import Problem, problems
from .judging import chain, make_example, majority, votes
from .records import approval, expected, solver_truth, sound, terminal
from .storage import RESULTS, STATE, Journal, adapter, append, read_json, retain, rows, stamp, write_json


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
    needed = [p for i, p in enumerate(pool) if i % 4 == 0 and p.key not in saved]
    for offset in range(0, len(needed), 4):
        batch = needed[offset:offset+4]
        seed = stream_seed("corpus", run.corpus, batch[0].key)
        traces = backend.generate([backend.prompt("solver", p) for p in batch], origin.name if origin else None,
                                  "corpus_solver", seed, True)
        histories = chain(backend, batch, traces, origin.judges if origin else (None,)*3, 2, seed)
        for p, t, h in zip(batch, traces, histories, strict=True):
            entry = {"key": p.key, "expression": p.expression, "trace": t, "reports": h}
            append(path, entry)
            saved[p.key] = entry
    return saved


def training_data(backend, run, count):
    pool = problems("train", max(32, count))
    natural = corpus(backend, run, pool) if run.role != "solver" else {}
    records = []
    for i, p in enumerate(pool):
        trace, history = ("", []) if run.role == "solver" else make_example(p, run.role, i, natural.get(p.key))
        records.append(dict(prompt=backend.prompt(run.role, p, trace, history), expression=p.expression,
                            trace=trace, history_json=json.dumps(history)))
    return Dataset.from_list(records)


class Reward:
    """Supply only the assigned training signal while separately writing oracle observations."""

    def __init__(self, backend, run):
        self.backend, self.run = backend, run
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
            if run.reward == "oracle":
                rewards = labels.copy()
            elif run.reward == "flat":
                histories = votes(self.backend, dataset, completions, seed, run.judges)
                rewards = [majority(h) for h in histories]
            else:
                depth = {"d1": 1, "d2": 2}.get(run.reward, 3)
                histories = chain(self.backend, dataset, completions, run.judges, depth, seed)
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
    def __init__(self, backend, run, steps):
        self.backend, self.run, self.steps = backend, run, steps
        self.started = None

    def on_train_begin(self, args, state, control, **kwargs):
        self.started = time.monotonic()

    def on_log(self, args, state, control, logs=None, **kwargs):
        if logs:
            values = {k: (v if math.isfinite(v) else None) for k, v in logs.items() if isinstance(v, (int, float))}
            append(RESULTS / self.run.name / "metrics.jsonl", dict(step=state.global_step, time=stamp(), **values))

    def on_step_end(self, args, state, control, **kwargs):
        if self.run.name == "timing" or state.global_step % 32 or self.run.role != "solver":
            return
        batch = problems("dev", 8)
        answers = self.backend.generate([self.backend.prompt("solver", p) for p in batch], "@active",
                                        "development_solver", 911, False)
        correct = sum(solver_truth(p, t)[0] for p, t in zip(batch, answers, strict=True))
        append(RESULTS / self.run.name / "metrics.jsonl", dict(step=state.global_step, time=stamp(),
               development_accuracy=correct/len(batch), development_n=len(batch)))


def train(run, steps):
    out = RESULTS / run.name
    finished = read_json(out / "trained.json")
    if finished and (adapter(run.name) / "adapter_config.json").is_file():
        return finished
    journal = Journal(run.name)
    backend = Backend(journal, run.initial, frozen_sources(run), run.seed)
    backend.label = run.role
    data = training_data(backend, run, steps)
    work = STATE / "runs" / run.name / "trainer"
    work.mkdir(parents=True, exist_ok=True)
    resume = get_last_checkpoint(str(work))
    completed = read_json(Path(resume)/"trainer_state.json") if resume else {}
    last_step = completed.get("global_step", 0)
    retain(out / "rollouts.jsonl", lambda row: row["step"] < last_step)
    retain(out / "metrics.jsonl", lambda row: row["step"] <= last_step)
    args = GRPOConfig(output_dir=str(work), max_steps=steps, per_device_train_batch_size=1,
                      gradient_accumulation_steps=4, num_generations=4, num_iterations=1, loss_type="grpo",
                      beta=0.0, epsilon=0.2, scale_rewards="group", learning_rate=3e-5, lr_scheduler_type="constant",
                      max_completion_length=48, temperature=0.8, top_p=1.0, top_k=0, bf16=True,
                      seed=run.seed, data_seed=run.seed, gradient_checkpointing=True,
                      gradient_checkpointing_kwargs={"use_reentrant": False}, optim="adamw_torch",
                      save_strategy="steps", save_steps=min(8, steps), save_total_limit=2, logging_steps=1,
                      report_to="none", disable_tqdm=True, remove_unused_columns=False, dataloader_num_workers=0)
    monitor = Metrics(backend, run, steps)
    trainer = GRPOTrainer(model=backend.model, args=args, processing_class=backend.tokenizer, train_dataset=data,
                          reward_funcs=Reward(backend, run), callbacks=[monitor])
    before = frozen_fingerprint(backend.model)
    write_json(out / "recipe.json", {"run": asdict(run), "updates": steps, "group": 4, "started": stamp()})
    journal.event("training_start", resume=resume, updates=steps, completed=last_step)
    trainer.train(resume_from_checkpoint=resume)
    elapsed = time.monotonic()-monitor.started
    after = frozen_fingerprint(backend.model)
    if before != after:
        raise RuntimeError("Frozen judge adapter changed during optimization")
    backend.model.save_pretrained(adapter(run.name), selected_adapters=["default"])
    result = dict(time=stamp(), run=asdict(run), updates=trainer.state.global_step,
                  elapsed_seconds=elapsed, resumed_at=last_step, frozen_checksum=after, usage=backend.totals)
    write_json(out / "trained.json", result)
    if run.name == "timing":
        seconds = elapsed / max(1, steps-last_step)
        count = max((n for n in (16,32,64,128,256) if 32*n*seconds <= 0.6*7*86400 and n*seconds <= 12*3600), default=16)
        write_json(RESULTS / "budget.json", dict(updates=count, seconds_per_update=seconds, time=stamp()))
    return result
