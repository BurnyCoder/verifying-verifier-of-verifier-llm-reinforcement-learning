"""A fixed difficulty ladder and fresh hash partitions for the learnability experiment."""

import hashlib
import random
from functools import lru_cache

from .domain import Problem, _expression, partition, problems

FAMILIES = ("one", "two-add", "two-mixed", "registered")
STYLES = ("registered", "demonstrated")
EXAMPLES = ("2+3", "(2+3)*4", "(4+3)*2")


@lru_cache(maxsize=1)
def excluded_keys():
    return {p.key for p in problems("train",256)} | {Problem.from_expression(e).key for e in EXAMPLES}


def phase_for(problem):
    """Assign the whole expression before generating any trace, prompt or altered review."""
    if partition(problem)!="train" or problem.key in excluded_keys():
        return None
    digest=hashlib.sha256(("learnability-v1|"+problem.key).encode()).hexdigest()
    bucket=int(digest[:12],16)%100
    for stop,phase in ((40,"train"),(50,"screen"),(60,"confirm"),(70,"validation"),(100,"benchmark")):
        if bucket<stop:
            return phase


def expression(family, rng):
    if family=="registered":
        return _expression(rng,rng.randint(3,5))
    if family=="one":
        return f"{rng.randrange(256)} {rng.choice(('+','-'))} {rng.randint(1,31)}"
    if family=="two-add":
        a,b,c=rng.randrange(60),rng.randint(1,12),rng.randint(1,12)
        first,second=rng.choice(("+","-")),rng.choice(("+","-"))
    elif family=="two-mixed":
        a,b,c=rng.randint(-12,39),rng.randint(1,12),rng.randint(1,12)
        first,second=rng.choice(("+","-")),"*"
        if rng.randrange(2):
            first,second=second,first
    else:
        raise ValueError(f"Unknown difficulty family {family}")
    return f"({a} {first} {b}) {second} {c}"


@lru_cache(maxsize=64)
def curriculum_problems(family, phase, count):
    rng=random.Random(f"learnability-v1|{phase}|{family}")
    found={}
    for _ in range(max(50000,500*count)):
        if len(found)==count:
            return tuple(found.values())
        p=Problem.from_expression(expression(family,rng))
        if phase_for(p)==phase:
            found.setdefault(p.key,p)
    raise ValueError(f"Requested {count} distinct {family}/{phase} problems, found {len(found)}")
