"""Freeze the development decision and route the amended comparisons to disjoint data."""

import hashlib
from functools import lru_cache

from .curriculum import FAMILIES, STYLES, curriculum_problems
from .storage import RESULTS, TRACK, read_json, write_json


def freeze_profile(original):
    """Make every calibrated arm depend on the same recorded positive-control result."""
    root = original / "learnability"
    sources = [root / (phase+".json") for phase in ("screen", "confirm", "learning")]
    screen, confirmation, learning = [read_json(path, {}) for path in sources]
    chosen = screen.get("selected") or {}
    family, style = chosen.get("family"), chosen.get("style")
    cell = confirmation.get("cell", {})
    if (family not in FAMILIES or style not in STYLES or not confirmation.get("confirmed") or
            (family, style) != (cell.get("family"), cell.get("style"))):
        raise RuntimeError("The chosen arithmetic and prompt setting requires independent confirmation")
    if learning.get("status") != "complete" or not learning.get("demonstrated"):
        raise RuntimeError("The registered held-out learning criterion has not been met")
    sources.append(original / "budget.json")
    budget = read_json(sources[-1])
    if not budget or budget.get("updates", 0) <= 0:
        raise RuntimeError("The original training budget is missing")
    profile = dict(family=family, style=style, updates=budget["updates"], sources={
        path.relative_to(original).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in sources})
    scope = original / "calibrated"
    for path, value in ((scope/"profile.json", profile), (scope/"budget.json", budget)):
        if path.exists() and read_json(path) != value:
            raise RuntimeError(f"Recorded benchmark decision changed at {path}")
    write_json(scope/"budget.json", budget)
    if not (scope/"profile.json").is_file():
        write_json(scope/"profile.json", profile)
    return profile


def active_profile():
    if TRACK == "original":
        return {}
    profile = read_json(RESULTS / "profile.json")
    if not profile:
        raise RuntimeError("Start the calibrated campaign after the learning control qualifies")
    return profile


@lru_cache(maxsize=4)
def reserved(family):
    return curriculum_problems(family, "benchmark", 2048+128)


def population(profile, split, count):
    """Use a common canonical prefix across arms and reserve a disjoint mechanism cohort."""
    if not profile or split in ("layout", "long"):
        return None
    family = profile["family"]
    if split == "dev":
        return curriculum_problems(family, "confirm", count)
    if split == "test":
        return reserved(family)[:count]
    if split == "mechanism":
        return reserved(family)[2048:2048+count]
    if split == "original-difficulty":
        if family == "registered":
            return reserved(family)[:count]
        # Some two-step expressions also occur in the original signed generator.
        omit = {p.key for p in reserved(family)}
        pool = curriculum_problems("registered", "benchmark", count+len(omit))
        return tuple(p for p in pool if p.key not in omit)[:count]
    raise ValueError(f"Unknown calibrated evaluation {split}")
