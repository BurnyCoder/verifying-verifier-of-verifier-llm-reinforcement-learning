"""Reconstruct scores, input histories and evidence interventions from closed GPU journals."""

from .domain import Problem
from .frozen_cases import metrics
from .learning_review import execute_steps
from .prompts import messages
from .records import expected, mask_evidence, parse, render, solver_truth, sound, terminal
from .storage import rows


def audit(folder, receipt):
    """Audit the scored output boundary without interpreting the server's prefilling as model text."""
    data = list(rows(folder/"cases.jsonl"))
    calls = {r["id"]:r for r in rows(folder/"calls.jsonl")}
    example = {}
    counter = 0
    identical_masked = 0

    def checked(call_id,level,p,trace,history):
        nonlocal counter
        c = calls[call_id]
        if (c["messages"]!=messages(f"j{level}",p,trace,history,"demonstrated") or
                not isinstance(c["generated_token_ids"],list) or len(c["generated_token_ids"])>48):
            raise ValueError(f"Unmatched prompt or token budget in {folder.name}/{call_id}")
        counter+=1
        return c
    for r in sorted(data,key=lambda x:(x["key"],x["kind"])):
        p = Problem.from_expression(r["expression"])
        if p.key!=r["key"] or tuple(execute_steps(p))!=p.values:
            raise ValueError("Independent arithmetic evaluator disagrees")
        if r["kind"]=="twins":
            masked = []
            for mode in ("visible","masked"):
                passed = True
                for i,review in enumerate(r["reviews"]):
                    actual = review if mode=="visible" else mask_evidence(review)
                    c = checked(f"{r['id']}/{mode}/{i}",3,p,r["trace"],[r["first"],actual])
                    truth = expected(p,r["trace"],[r["first"],review])
                    if c["text"]!=r[mode]["outputs"][i] or list(truth)!=r["labels"][i]:
                        raise ValueError("Logged judge output or exact reference changed")
                    passed &= sound(c["text"],truth)
                    if mode=="masked":
                        masked.append(c)
                if passed!=r[mode]["correct"]:
                    raise ValueError("Recorded whole-pair grade disagrees with raw generations")
            if masked[0]["rendered_prompt"]!=masked[1]["rendered_prompt"]:
                raise ValueError("The mask did not remove the distinguishing evidence")
            identical_masked += masked[0]["generated_token_ids"]==masked[1]["generated_token_ids"]
            outcome = "passed" if r["visible"]["correct"] else "failed"
            example.setdefault(outcome,dict(key=p.key,expression=p.expression,trace=r["trace"],first=r["first"],
                                       reviews=r["reviews"],outputs=r["visible"]["outputs"],expected=[render(v) for v in r["labels"]]))
        else:
            verdict = solver_truth(p,r["trace"])[0]
            history = []
            for level in (1,2,3):
                c = checked(f"{r['id']}/j{level}",level,p,r["trace"],history)
                truth = expected(p,r["trace"],history)
                bit = terminal(c["text"],level)
                grade = dict(verdict=bit,agreement=int(bit==verdict),full=int(sound(c["text"],truth)),
                             malformed=parse(c["text"],len(truth)) is None,expected=list(truth))
                if grade!=r["grades"][level-1] or c["text"]!=r["reports"][level-1] or verdict!=r["valid"]:
                    raise ValueError("Logged chain disagrees with executable rescore")
                history.append(c["text"])
    if metrics(data)!=receipt["metrics"] or counter!=receipt["cost"]["calls"] or len(calls)!=counter+4:
        raise ValueError("Published summary disagrees with complete raw observations")
    return dict(calls=counter,matched_masked_outputs=identical_masked,examples=example)
