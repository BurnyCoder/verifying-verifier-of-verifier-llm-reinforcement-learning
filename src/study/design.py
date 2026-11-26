"""One dependency-ordered manifest drives training, publication, and analysis."""

from dataclasses import dataclass

SEEDS = (17, 29, 43)
PILOTS = ("learn-oracle-17","learn-shuffle-17")
BASE = "Qwen/Qwen2.5-1.5B-Instruct"
REVISION = "989aa7980e4cf806f80c7fef2b1adb7bc71aa306"
PROJECT = "verifying-verifier-of-verifier-llm-reinforcement-learning"
GITHUB = f"https://github.com/BurnyCoder/{PROJECT}"
PAGES = f"https://burnycoder.github.io/{PROJECT}/"


@dataclass(frozen=True)
class Run:
    name: str
    seed: int = 17
    role: str = "solver"
    reward: str = "d3"
    judges: tuple = (None, None, None)
    initial: str | None = None
    teacher: str | None = None
    corpus: str = "base"
    family: str | None = None
    prompt_style: str = "registered"

    @property
    def dependencies(self):
        sources = (*self.judges, self.initial, self.teacher, None if self.corpus == "base" else self.corpus)
        return tuple(dict.fromkeys(x for x in sources if x))


def matrix():
    rows = [Run(f"{arm}-17", reward=arm) for arm in ("d3", "d2", "d1", "flat", "oracle", "hybrid", "shuffle")]
    direct = tuple(f"exact-j{i}" for i in (1, 2, 3))
    top = ("top-j1", "top-j2", direct[2])
    rows.extend(Run(name, role=f"j{i}", reward="exact") for i, name in enumerate(direct, 1))
    rows.extend((Run(top[1], role="j2", reward="teacher", teacher=direct[2]),
                 Run(top[0], role="j1", reward="teacher", teacher=top[1])))
    for route, judges in (("exact", direct), ("top", top)):
        for prefix in (1, 2, 3):
            rows.append(Run(f"{route}-prefix{prefix}", judges=judges[:prefix]+(None,)*(3-prefix)))
    for route, judges in (("exact", direct), ("top", top)):
        current = list(judges)
        corpus = f"{route}-prefix3"
        for index in ((0, 1, 2) if route == "exact" else (2, 1, 0)):
            name = f"alt-{route}-j{index+1}"
            teacher = current[index+1] if route == "top" and index < 2 else None
            rows.append(Run(name, role=f"j{index+1}", reward="teacher" if teacher else "exact",
                            teacher=teacher, initial=current[index], corpus=corpus))
            current[index] = name
        rows.append(Run(f"alt-{route}-solver", judges=tuple(current), initial=corpus, corpus=corpus))
    rows.extend(Run(f"{arm}-{seed}", seed=seed, reward=arm) for seed in SEEDS[1:] for arm in ("d3", "d2", "flat"))
    return rows


def permute_groups(values, rng):
    if len(values) % 4:
        raise ValueError("A shuffled GRPO reward requires complete groups of four")
    result = []
    for offset in range(0, len(values), 4):
        group = list(values[offset:offset+4])
        rng.shuffle(group)
        result.extend(group)
    return result
