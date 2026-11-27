"""Screen immutable, GPU-resident judge models before confirming a selection on fresh problems."""

from contextlib import ExitStack
from dataclasses import replace
from statistics import mean

from .curriculum import curriculum_problems
from .domain import Problem
from .frozen_cases import CaseRunner, metrics, paired_confirmation
from .frozen_gpu import BUILD, CONTEXT, LIMIT, GPUFitError, LocalCUDA, weight_file
from .frozen_models import LOCAL_REPLICATES, MODELS, SMALLER_FILES
from .storage import ORIGINAL_RESULTS, Journal, log_directory, read_json, rows, stamp, write_json


ROOT = ORIGINAL_RESULTS / "new-judges"


def configurations(model):
    yield model
    for filename,digest,size in SMALLER_FILES.get(model.key,()):
        yield replace(model,filename=filename,sha256=digest,size=size)


def run_one(key, model, phase, confirmed_file=None):
    folder = ROOT/key
    marker = folder/"result.json"
    if marker.is_file():
        return read_json(marker)
    folder.mkdir(parents=True,exist_ok=True)
    profile = read_json(ORIGINAL_RESULTS/"calibrated/profile.json")
    if not profile:
        raise RuntimeError("The calibrated arithmetic profile is required for newer-judge comparisons")
    journal = Journal("new-judges-"+key)
    registration = read_json(folder/"configuration.json",{})
    fit_attempts = read_json(folder/"fit.json",[])
    choices = list(configurations(model))
    expected_file = confirmed_file or registration.get("file")
    if expected_file:
        choices = [c for c in choices if c.filename==expected_file]
    if not choices:
        raise ValueError(f"Unknown registered quantization {expected_file}")
    write_json(folder/"progress.json",dict(time=stamp(),status="Checking GPU fit",model=model.title,phase=phase))
    def finish(status, description, **data):
        result = dict(time=stamp(),phase=phase,model=model.title,status=status,result=description,**data)
        write_json(marker,result)
        journal.event("result",**result)
        return result
    with ExitStack() as stack:
        for config in choices:
            path = weight_file(config)
            logfile = log_directory()/("new-judges-"+key)/(stamp().replace(":","-")+"-server.log")
            template = None
            if config.repository.startswith("ollama/"):
                from huggingface_hub import hf_hub_download
                template = hf_hub_download("Qwen/"+model.title,"chat_template.jinja",revision=config.base_revision)
            try:
                backend = stack.enter_context(LocalCUDA(path,logfile,template))
            except GPUFitError as e:
                fit_attempts.append(dict(time=stamp(),file=config.filename,fit=False,reason=str(e)))
                write_json(folder/"fit.json",fit_attempts)
                journal.event("fit_failed",file=config.filename,reason=str(e))
                continue
            fit_attempts.append(dict(time=stamp(),file=config.filename,fit=True,placement=backend.placement))
            write_json(folder/"fit.json",fit_attempts)
            break
        else:
            if registration:
                raise RuntimeError("Previously verified GPU configuration is currently unavailable. Resume the same file.")
            return finish("GPU fit unavailable","No full-GPU configuration passed placement checks",fit=fit_attempts)
        protocol = dict(model=config.title,repository=config.repository,revision=config.revision,file=config.filename,
                        sha256=config.sha256,base_revision=config.base_revision,build=BUILD,context=CONTEXT,
                        output_limit=LIMIT,phase=phase,decoder="greedy, thinking disabled, raw generated tokens",placement="CUDA0")
        if registration and registration != protocol:
            raise ValueError("Frozen judge execution configuration changed on resume")
        write_json(folder/"configuration.json",protocol)
        runner = CaseRunner(folder,backend,config.sha256+"|"+BUILD+"|raw-v2|"+phase,journal.event)
        demo = Problem.from_expression("(4+3)*2")
        for i,(level,history) in enumerate(((1,[]),(2,["0,1,7"]),(3,["0,1,7","1,0,7,0,1,7"]),
                                             (3,["0,1,7","1,0,6,0,1,7"]))):
            runner.ask(f"timing/{i}",level,demo,"8,14",history)
        timing = mean(runner.calls[f"timing/{i}"]["elapsed_seconds"] for i in range(4))
        if timing>30:
            return finish("Timing only",f"{timing:.2f} seconds per pilot call",file=config.filename,timing_seconds=timing)
        start, stop = (256,320) if phase=="confirmation" else (96,128)
        pool = curriculum_problems(profile["family"],"confirm",stop)[start:stop]
        natural = []
        if phase!="confirmation":
            natural = list(rows(ORIGINAL_RESULTS/"calibrated/base/replay.jsonl"))
            if len(natural)!=32 or len({r["key"] for r in natural})!=32 or {p.key for p in pool}&{r["key"] for r in natural}:
                raise ValueError("Expected 32 unique archived traces disjoint from the balanced screen")
        def progress():
            write_json(folder/"progress.json",dict(time=stamp(),status="Evaluating",model=config.title,phase=phase,
                       file=config.filename,calls=len(runner.calls),target=4+3*len(natural)+10*len(pool),
                       cases=len(runner.completed),timing_seconds=timing))
        progress()
        for r in natural:
            problem = Problem.from_expression(r["expression"])
            if problem.key!=r["key"]:
                raise ValueError("The archived problem hash changed")
            runner.chain("natural",problem,r["trace"])
            progress()
        for i,problem in enumerate(pool):
            runner.balanced(problem,i)
            runner.twins(problem,i)
            progress()
        values = metrics(runner.completed.values())
        n = len(pool)
        if (values["balanced"]["n"]!=2*n or values["twins"]["n"]!=n or len(runner.calls)!=4+3*len(natural)+10*n):
            raise ValueError("Incomplete frozen-judge cohort")
        balanced, twins = values["balanced"], values["twins"]
        calls = [r for k,r in runner.calls.items() if not k.startswith("timing/")]
        cost = {field:sum(r[field] for r in calls) for field in ("input_tokens","output_tokens","elapsed_seconds")}
        cost.update(calls=len(calls),prompt_ms=sum(r["timings"].get("prompt_ms",0) for r in calls),
                    generation_ms=sum(r["timings"].get("predicted_ms",0) for r in calls))
        result = f"J3 verdict {balanced['depths'][2]['correct']}/{2*n}, twins {twins['visible']}/{n}, masked {twins['masked']}/{n}"
        return finish("Complete",result,file=config.filename,metrics=values,cost=cost,timing_seconds=timing)


def campaign(publish=False):
    """Release every measured configuration even if its model only completed a fit/timing pilot."""
    from .cli import study_lock,worker
    def stage(key,model,phase,confirmed_file=None):
        outcome = run_one(key,model,phase,confirmed_file)
        if publish:
            worker("publish","--milestone","new-judges-"+key)
        else:
            worker("report")
        return outcome
    with study_lock("frozen-judge-suite"):
        for m in LOCAL_REPLICATES:
            stage(m.key,m,"deployment replicate")
        results = {m.key:stage(m.key,m,"screen") for m in MODELS}
        eligible = [m for m in MODELS[1:] if results[m.key]["status"]=="Complete"]
        if not eligible or results[MODELS[0].key]["status"]!="Complete":
            decision = dict(status="No matched confirmation",result="No eligible newer model and same-runtime control pair")
        else:
            def rank(m):
                result = results[m.key]
                return (result["metrics"]["twins"]["visible"],result["metrics"]["balanced"]["depths"][2]["accuracy"],
                        -result["cost"]["elapsed_seconds"])
            winner = max(eligible,key=rank)
            confirmation = [stage(key,m,"confirmation",results[m.key]["file"]) for key,m in
                            (("confirm-control",MODELS[0]),("confirm-winner",winner))]
            if not all(r["status"]=="Complete" for r in confirmation):
                decision = dict(status="Confirmation incomplete",selected=winner.key,result="No paired confirmation estimate")
            else:
                def cases(key):
                    return {r["id"]:r for r in rows(ROOT/key/"cases.jsonl")}
                estimates = paired_confirmation(cases("confirm-winner"),cases("confirm-control"))
                gate = all(e["delta"]>0 for e in estimates.values())
                decision = dict(status="Confirmed comparison",selected=winner.key,estimates=estimates,online_gate=gate,
                                result="Online comparison eligible on a later day" if gate else "Online improvement gate did not pass")
        write_json(ROOT/"decision.json",dict(time=stamp(),**decision))
        if publish:
            worker("publish","--milestone","new-judges-decision")
        else:
            worker("report")
        return decision
