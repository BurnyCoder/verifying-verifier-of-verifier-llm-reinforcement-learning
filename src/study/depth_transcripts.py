"""Verify the role prompts, sampled outputs and actually evaluated weights from the full local journals."""

import argparse
import hashlib
from pathlib import Path

from .domain import Problem
from .storage import ORIGINAL_STATE, ROOT, read_json, rows, write_json


def verify_arm(project, state, depth, seed):
    """Reconcile the raw tokenizer stream with each solver and reviewer row in optimizer order."""
    name = f"d{depth}-{seed}"
    target = project/"results/calibrated"/name
    with (state/"calibrated/runs"/name/"adapter/adapter_model.safetensors").open("rb") as file:
        weights = hashlib.file_digest(file,"sha256").hexdigest()
    if read_json(target/"development.json")["weights"] != weights:
        raise ValueError(f"{name} development used different adapter bytes")
    training = list(rows(target/"rollouts.jsonl"))
    roles = ["solver",*[f"j{i}" for i in range(1,depth+1)]]
    journal = {(event,role): [] for role in roles for event in ("prompts","outputs")}
    sources = {}
    for path in sorted((project/"logs/calibrated"/name).glob("*.jsonl")):
        with path.open("rb") as file:
            sources[path.name] = hashlib.file_digest(file,"sha256").hexdigest()
        for event in rows(path):
            if event["event"] == "training_start":
                # Resume discards uncheckpointed rollouts in the training table and starts those groups again.
                for values in journal.values():
                    del values[4*event["completed"]:]
            key = (event["event"],event.get("role"))
            if key in journal:
                journal[key].extend(event["text"])
    if not sources or not training:
        raise ValueError(f"Missing local journals or training rows for {name}")
    for index, role in enumerate(roles):
        prompts, outputs = (journal[key,role] for key in ("prompts","outputs"))
        for prompt, output, r in zip(prompts,outputs,training,strict=True):
            question = Problem.from_expression(r["expression"]).question
            answer = r["answer"] if index == 0 else r["reports"][index-1]
            actual = output.replace("<|im_end|>","").replace("<|endoftext|>","")
            last_turn = prompt.split("<|im_start|>user\n")[-1]
            if actual != answer or not last_turn.startswith(question+"\n"):
                raise ValueError(f"{name}/{role} response or question mismatch at step {r['step']}")
            if index:
                submitted = question+"\nSolver response: "+r["answer"]
                for prior in range(index-1):
                    submitted += f"\nJudge {prior+1}: {r['reports'][prior]}"
                if not last_turn.startswith(submitted+f"\nYour Judge {index} record:"):
                    raise ValueError(f"{name}/{role} input history mismatch at step {r['step']}")
    return dict(adapter_sha256=weights, journals_sha256=sources, training_answers=len(training),
                matched_calls=len(training)*len(roles))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed",type=int,required=True)
    parser.add_argument("--project",type=Path,default=ROOT)
    parser.add_argument("--state",type=Path,default=ORIGINAL_STATE)
    parser.add_argument("--output",type=Path)
    args = parser.parse_args()
    arms = {f"d{depth}-{args.seed}": verify_arm(args.project,args.state,depth,args.seed) for depth in (2,3)}
    out = args.output or args.project/f"results/calibrated/diagnostics/depth-transcripts-{args.seed}.json"
    write_json(out,dict(seed=args.seed,arms=arms))
    print(out)


if __name__ == "__main__":
    main()
