"""Preregistered selection and checkpoint-conditional paired comparisons for the pilot."""

from statistics import mean

import numpy as np

from .curriculum import FAMILIES, STYLES


def cell_metrics(records, family, style):
    sample=[v for r in records for v in r["sampled_correct"]]
    return dict(family=family,style=style,problems=len(records),samples=len(sample),sampled_exact=mean(sample),
                greedy_exact=mean(r["greedy_correct"] for r in records),
                parsed=mean(v for r in records for v in r["sampled_parsed"]),
                mixed_groups=sum(len(set(r["sampled_correct"]))==2 for r in records))


def choose_cell(cells):
    eligible=[c for c in cells if c["problems"]==16 and c["parsed"]>=.75 and
              .15<=c["sampled_exact"]<=.85 and .10<=c["greedy_exact"]<=.90 and c["mixed_groups"]>=2]
    return min(eligible,key=lambda c:(abs(c["sampled_exact"]-.5),-c["mixed_groups"],-c["parsed"],
               FAMILIES.index(c["family"]),STYLES.index(c["style"])),default=None)


def confirmed(cell):
    return (cell["problems"]==48 and cell["parsed"]>=.60 and .05<=cell["sampled_exact"]<=.95
            and cell["mixed_groups"]>=1)


def paired_change(after,before):
    keys=sorted(before)
    d=np.array([after[k]-before[k] for k in keys],dtype=float)
    rng=np.random.default_rng(20261126)
    boot=np.concatenate([d[rng.integers(len(d),size=(100,len(d)))].mean(axis=1) for _ in range(100)])
    return dict(n=len(d),delta=float(d.mean()),interval=np.quantile(boot,[.025,.975]).tolist(),
                fixed=int((d>0).sum()),harmed=int((d<0).sum()))


def changes_by_parse(after, before):
    """Partition the paired accuracy change; choose the first canonical example per kind."""
    if before.keys() != after.keys():
        raise ValueError("Parse transitions require identical problem IDs")
    labels = {(True,True):"Both parsed", (True,False):"Only trained parsed",
              (False,True):"Only comparator parsed", (False,False):"Neither parsed"}
    counts = {label:dict(stratum=label, n=0, gains=0, losses=0) for label in labels.values()}
    examples = {}
    for key in sorted(before):
        trained, comparator = after[key], before[key]
        label = labels[bool(trained["parsed"]), bool(comparator["parsed"])]
        counts[label]["n"] += 1
        change = trained["correct"] - comparator["correct"]
        if change:
            direction = "gain" if change > 0 else "loss"
            counts[label]["gains" if change > 0 else "losses"] += 1
            examples.setdefault((label,direction),dict(key=key, stratum=label, change=direction,
                expression=trained["expression"], expected=trained["expected_values"],
                comparator=comparator["trace"], trained=trained["trace"]))
    return dict(groups=list(counts.values()), examples=list(examples.values()))


def learning_result(base,exact,shuffled):
    if len(base)!=256 or base.keys()!=exact.keys() or base.keys()!=shuffled.keys():
        return {"status":"pending"}
    gain,control=paired_change(exact,base),paired_change(exact,shuffled)
    demonstrated=gain["delta"]>=.05 and gain["interval"][0]>0
    return dict(status="complete",demonstrated=demonstrated,reward_specific=demonstrated and control["interval"][0]>0,
                over_base=gain,over_shuffled=control)
