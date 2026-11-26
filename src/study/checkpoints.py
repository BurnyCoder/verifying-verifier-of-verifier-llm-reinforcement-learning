"""Recover a fully written single-process TRL update after interruption."""

import json


def last_complete(directory):
    """Trainer saves its JSON state after weights, optimizer, scheduler and RNG state."""
    # See transformers.Trainer._save_checkpoint, https://huggingface.co/docs/transformers/main_classes/trainer
    candidates = []
    for path in directory.glob("checkpoint-*"):
        suffix = path.name.removeprefix("checkpoint-")
        if path.is_dir() and suffix.isdigit():
            candidates.append((int(suffix), path))
    for step, path in sorted(candidates, reverse=True):
        try:
            state = json.loads((path/"trainer_state.json").read_text(encoding="utf-8"))
            files = ("adapter_model.safetensors", "adapter_config.json", "optimizer.pt", "scheduler.pt", "rng_state.pth")
            if state.get("global_step") == step and all((path/name).stat().st_size for name in files):
                return path, step
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
    return None, 0
