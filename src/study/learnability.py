"""GPU calibration and paired positive-control evaluations on fresh training-partition problems."""

from statistics import mean

from .backend import Backend, stream_seed
from .curriculum import FAMILIES, STYLES, curriculum_problems
from .design import PILOTS, Run
from .evaluate import mechanisms, weights_digest
from .judging import chain
from .learnability_analysis import cell_metrics, changes_by_parse, choose_cell, confirmed, learning_result
from .records import expected, parse, render, solver_truth, sound, terminal
from .storage import RESULTS, Journal, append, generation_cost, read_json, rows, stamp, write_json

def directory():
    return RESULTS/"learnability"


def selected():
    result=read_json(directory()/"screen.json",{})
    if not result.get("selected"):
        raise ValueError("No frozen-model configuration passed the registered difficulty screen")
    return result["selected"]


def pilot_spec(name):
    if name not in PILOTS or not read_json(directory()/"confirm.json",{}).get("confirmed"):
        raise ValueError("A confirmed difficulty configuration is required for the learnability pilot")
    c=selected()
    return Run(name,reward="oracle" if name==PILOTS[0] else "oracle-shuffle",family=c["family"],prompt_style=c["style"])


def measure(backend,family,style,phase,count):
    """Keep groups of four identical prompts together and retain batch membership on recovery."""
    backend.prompt_style=style
    pool=curriculum_problems(family,phase,count)
    path=directory()/phase/(family+"-"+style+".jsonl")
    saved={r["key"] for r in rows(path)}
    for offset in range(0,count,4):
        batch=pool[offset:offset+4]
        if all(p.key in saved for p in batch):
            continue
        prompts=[backend.prompt("solver",p) for p in batch]
        seed=stream_seed("learnability",phase,family,offset)
        greedy=backend.generate(prompts,None,"greedy_solver",seed,False)
        sampled=backend.generate([q for q in prompts for _ in range(4)],None,"sampled_solver",seed,True)
        for i,p in enumerate(batch):
            if p.key in saved:
                continue
            group=sampled[4*i:4*i+4]
            append(path,dict(key=p.key,expression=p.expression,expected_values=p.values,greedy=greedy[i],
                             greedy_correct=solver_truth(p,greedy[i])[0],sampled=group,
                             sampled_correct=[solver_truth(p,t)[0] for t in group],
                             sampled_parsed=[parse(t,len(p.values)) is not None for t in group]))
    return cell_metrics(list(rows(path)),family,style)


def screen():
    target=directory()/"screen.json"
    if target.exists():
        return read_json(target)
    backend=Backend(Journal("learnability-screen"))
    cells=[measure(backend,family,style,"screen",16) for family in FAMILIES for style in STYLES]
    outcome=dict(time=stamp(),cells=cells,selected=choose_cell(cells),**generation_cost("learnability-screen",backend.totals))
    write_json(target,outcome)
    return outcome


def confirm():
    target=directory()/"confirm.json"
    if target.exists():
        return read_json(target)
    c=selected()
    backend=Backend(Journal("learnability-confirm"))
    measurement=measure(backend,c["family"],c["style"],"confirm",48)
    outcome=dict(time=stamp(),cell=measurement,confirmed=confirmed(measurement),**generation_cost("learnability-confirm",backend.totals))
    write_json(target,outcome)
    return outcome


def audit():
    target=directory()/"audit.json"
    if target.exists():
        return read_json(target)
    spec=pilot_spec(PILOTS[0])
    backend=Backend(Journal("learnability-audit"))
    backend.prompt_style=spec.prompt_style
    pool=curriculum_problems(spec.family,"confirm",16)
    path=directory()/"balanced-reviews.jsonl"
    done={(r["key"],r["valid"]) for r in rows(path)}
    for offset in range(0,len(pool),4):
        batch,traces=[],[]
        for i,p in enumerate(pool[offset:offset+4],offset):
            altered=list(p.values)
            altered[i%len(altered)]+=1
            twins=[render(p.values),render(altered)]
            batch.extend([p,p])
            traces.extend(twins[::-1] if i%2 else twins)
        if all((p.key,solver_truth(p,t)[0]) in done for p,t in zip(batch,traces,strict=True)):
            continue
        histories=chain(backend,batch,traces,(None,)*3,3,stream_seed("balanced",offset))
        for p,t,h in zip(batch,traces,histories,strict=True):
            valid=solver_truth(p,t)[0]
            if (p.key,valid) not in done:
                append(path,dict(key=p.key,expression=p.expression,trace=t,valid=valid,reports=h,
                                 verdicts=[terminal(a,i+1) for i,a in enumerate(h)],
                                 evidence=[sound(a,expected(p,t,h[:i])) for i,a in enumerate(h)],
                                 malformed=[parse(a,3 if i==0 else 6) is None for i,a in enumerate(h)]))
    records=list(rows(path))
    levels=[]
    for i in range(3):
        pos=[r for r in records if r["valid"]]
        neg=[r for r in records if not r["valid"]]
        sensitivity=mean(r["verdicts"][i] for r in pos)
        specificity=mean(1-r["verdicts"][i] for r in neg)
        levels.append(dict(level=i+1,valid=len(pos),invalid=len(neg),sensitivity=sensitivity,specificity=specificity,
                           balanced_accuracy=(sensitivity+specificity)/2,evidence=mean(r["evidence"][i] for r in records),
                           malformed=sum(r["malformed"][i] for r in records)))
    twin_path=directory()/"confirmation-twins.jsonl"
    mechanisms(backend,None,"learnability-confirm",len(pool),twin_path,population=pool)
    pairs=list(rows(twin_path))
    result=dict(time=stamp(),judges=levels,pairs=len(pairs),visible=mean(r["visible_pair"] for r in pairs),
                masked=mean(r["masked_pair"] for r in pairs),**generation_cost("learnability-audit",backend.totals))
    write_json(target,result)
    return result


def evaluate_pilot(name):
    if name not in ("base",*PILOTS):
        raise ValueError(f"Unknown learnability evaluation {name}")
    where=directory()/"evaluations"
    target=where/(name+".json")
    if target.exists():
        return read_json(target)
    spec=pilot_spec(PILOTS[0])
    snapshot=None if name=="base" else name
    backend=Backend(Journal("learnability-"+name+"-evaluation"),frozen=[snapshot])
    backend.prompt_style=spec.prompt_style
    pool=curriculum_problems(spec.family,"validation",256)
    path=where/(name+".jsonl")
    saved={r["key"] for r in rows(path)}
    for offset in range(0,len(pool),8):
        batch=pool[offset:offset+8]
        if all(p.key in saved for p in batch):
            continue
        answers=backend.generate([backend.prompt("solver",p) for p in batch],snapshot,"validation_solver",
                                 stream_seed("learnability-validation",offset),False)
        for p,t in zip(batch,answers,strict=True):
            if p.key not in saved:
                append(path,dict(key=p.key,expression=p.expression,expected_values=p.values,trace=t,
                                 correct=solver_truth(p,t)[0],parsed=parse(t,len(p.values)) is not None))
    records=list(rows(path))
    result=dict(time=stamp(),n=len(records),correct=sum(r["correct"] for r in records),parsed=sum(r["parsed"] for r in records),
                weights=weights_digest(name) if snapshot else "frozen base",
                **generation_cost("learnability-"+name+"-evaluation",backend.totals))
    write_json(target,result)
    return result


def compare():
    where=directory()/"evaluations"
    samples=[{r["key"]:r for r in rows(where/(name+".jsonl"))}
             if (where/(name+".json")).is_file() else {} for name in ("base",*PILOTS)]
    result=learning_result(*({key:r["correct"] for key,r in records.items()} for records in samples))
    if result["status"]=="complete":
        base, trained, shuffled = samples
        result["by_parse"] = {"base":changes_by_parse(trained,base), "shuffled":changes_by_parse(trained,shuffled)}
        write_json(directory()/"learning.json",dict(time=stamp(),**result))
    return result
