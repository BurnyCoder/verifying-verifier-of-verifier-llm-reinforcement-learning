"""Replay frozen judges on fixed solver answers and paired evidence changes, with per-call resume."""

import hashlib
import json

import numpy as np

from .judging import twin
from .prompts import messages
from .records import expected, mask_evidence, parse, render, solver_truth, sound, terminal
from .storage import append, rows, stamp


class CaseRunner:
    def __init__(self, directory, backend, artifact, log):
        self.directory, self.backend, self.artifact, self.log = directory, backend, artifact, log
        self.calls = {r["id"]:r for r in rows(directory/"calls.jsonl")}
        self.completed = {r["id"]:r for r in rows(directory/"cases.jsonl")}
        if any(r["artifact"] != artifact for r in (*self.calls.values(), *self.completed.values())):
            raise ValueError("Frozen weights or registered inference configuration changed during resume")

    def ask(self, call_id, level, problem, trace, history):
        prompt = messages(f"j{level}",problem,trace,history,"demonstrated")
        digest = hashlib.sha256(json.dumps(prompt,ensure_ascii=False,separators=(",",":")).encode()).hexdigest()
        if call_id in self.calls:
            previous = self.calls[call_id]
            if previous["prompt_sha256"] != digest:
                raise ValueError(f"Changed prompt on resume for {call_id}")
            return previous["text"]
        self.log("prompts",call_id=call_id,role=f"j{level}",messages=prompt)
        observation = self.backend.generate(prompt)
        record = dict(id=call_id, artifact=self.artifact, role=f"j{level}", key=problem.key, messages=prompt,
                      time=stamp(),prompt_sha256=digest,**observation)
        self.log("outputs",**record)
        append(self.directory/"calls.jsonl",record)
        self.calls[call_id] = record
        return record["text"]

    def save(self, case_id, **fields):
        record = dict(id=case_id, time=stamp(), artifact=self.artifact, **fields)
        append(self.directory/"cases.jsonl", record)
        self.completed[case_id] = record

    def chain(self, cohort, p, trace):
        case_id = f"{cohort}/{p.key}"
        if case_id in self.completed:
            return
        reports, grades = [], []
        valid = solver_truth(p,trace)[0]
        for level in (1,2,3):
            output = self.ask(f"{case_id}/j{level}",level,p,trace,reports)
            truth = expected(p,trace,reports)
            verdict = terminal(output,level)
            grades.append(dict(verdict=verdict,agreement=int(verdict==valid),full=int(sound(output,truth)),
                               malformed=parse(output,len(truth)) is None, expected=truth))
            reports.append(output)
        self.save(case_id,kind=cohort,key=p.key,expression=p.expression,trace=trace,valid=valid,reports=reports,grades=grades)

    def balanced(self, p, index):
        self.chain("balanced-valid",p,render(p.values))
        values = list(p.values)
        values[index % len(values)] += 1
        self.chain("balanced-invalid",p,render(values))

    def twins(self, p, index):
        case_id = f"twins/{p.key}"
        if case_id in self.completed:
            return
        trace, first, good, bad = twin(p,index)
        labels = [expected(p,trace,[first,report]) for report in (good,bad)]
        conditions = {}
        for mode in ("visible","masked"):
            outputs = [self.ask(f"{case_id}/{mode}/{i}",3,p,trace,[first,report if mode=="visible" else mask_evidence(report)])
                       for i,report in enumerate((good,bad))]
            conditions[mode] = dict(outputs=outputs,correct=int(all(sound(o,label) for o,label in zip(outputs,labels,strict=True))))
        self.save(case_id,kind="twins",key=p.key,expression=p.expression,trace=trace,first=first,reviews=[good,bad],
                  labels=labels,**conditions)


def metrics(records):
    """Keep the original solution grade, the audit evidence, and the two-twin score distinct."""
    data = list(records)
    result = {}
    for label in ("natural", "balanced"):
        sample = [r for r in data if r["kind"].startswith(label)]
        depths = []
        for i in range(3):
            correct = sum(r["grades"][i]["agreement"] for r in sample)
            depths.append(dict(correct=correct,accuracy=correct/len(sample) if sample else None,
                full=sum(r["grades"][i]["full"] for r in sample), malformed=sum(r["grades"][i]["malformed"] for r in sample),
                false_accept=sum(not r["valid"] and r["grades"][i]["verdict"] for r in sample),
                false_reject=sum(r["valid"] and not r["grades"][i]["verdict"] for r in sample)))
        result[label] = dict(n=len(sample),valid=sum(r["valid"] for r in sample),depths=depths,
            fixed=sum(r["grades"][2]["agreement"] and not r["grades"][1]["agreement"] for r in sample),
            harmed=sum(r["grades"][1]["agreement"] and not r["grades"][2]["agreement"] for r in sample))
    pairs = [r for r in data if r["kind"]=="twins"]
    result["twins"] = dict(n=len(pairs), **{m:sum(r[m]["correct"] for r in pairs) for m in ("visible","masked")})
    return result


def paired_confirmation(candidate, control):
    """Bootstrap at the arithmetic-problem level, keeping both trace conditions together."""
    if candidate.keys() != control.keys():
        raise ValueError("Confirmation probes must use the same cases")
    keys = sorted(r["key"] for r in candidate.values() if r["kind"]=="twins")
    def values(records,key):
        return [records["twins/"+key]["visible"]["correct"],
                np.mean([records[f"balanced-{kind}/{key}"]["grades"][2]["agreement"] for kind in ("valid","invalid")])]
    diffs = np.array([np.subtract(values(candidate,k),values(control,k)) for k in keys])
    rng = np.random.default_rng(20261127)
    draws = diffs[rng.integers(len(keys),size=(10000,len(keys)))].mean(axis=1)
    return {measure:dict(n=len(keys),delta=float(diffs[:,i].mean()),ci=np.quantile(draws[:,i],[.025,.975]).tolist())
            for i,measure in enumerate(("twins","balanced_verdict"))}
