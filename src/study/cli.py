"""Normal research entry points for the local GPU, live monitoring, and public reports."""

import argparse
import contextlib
import json
import os
import subprocess
import sys
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from .benchmark import active_profile
from .design import MATCHED_NAMES, PILOTS, ROUTES, Run, matched_runs, matrix
from .online_solvers import NAMES as ONLINE_NAMES
from .storage import ORIGINAL_RESULTS, RESULTS, ROOT, STATE, TRACK, read_json, stamp, write_json


def run_spec(name):
    if name == "timing":
        return Run("timing")
    if name in PILOTS:
        from .learnability import pilot_spec
        return pilot_spec(name)
    if name in MATCHED_NAMES and TRACK!="calibrated":
        raise ValueError("The matched-depth solver runs require STUDY_TRACK=calibrated")
    profile=active_profile()
    return next(row for row in [*matrix(profile),*matched_runs(profile)] if row.name==name)


def worker(*args):
    """Keep independent training processes from retaining the previous arm's GPU allocations."""
    print(f"{stamp()} starting {' '.join(args)}", flush=True)
    command = [sys.executable, "-u", "-m", "study.cli", *args]
    if args[0] in ("train","evaluate"):
        from .monitor import supervise
        phase = "train" if args[0]=="train" else "final" if "--final" in args else "development"
        supervise(command, args[args.index("--run")+1], phase)
    elif args[0]=="publish":
        # A disconnected upload can be retried from the same immutable milestone and receipt.
        for attempt in range(3):
            result = subprocess.run(command)
            if result.returncode == 0:
                return
            if attempt == 2:
                result.check_returncode()
            delay = 15*(attempt+1)
            print(f"{stamp()} publication exited {result.returncode}, retrying the same milestone in {delay}s",flush=True)
            time.sleep(delay)
    else:
        subprocess.run(command,check=True)


@contextlib.contextmanager
def study_lock(name):
    """Use an OS-held lock that releases on crash or restart and prevents competing supervisors."""
    STATE.mkdir(parents=True,exist_ok=True)
    with (STATE/(name.replace("/", "--")+".lock")).open("a+b") as lock:
        lock.seek(0)
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        else:
            import fcntl
            fcntl.flock(lock,fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def campaign(public, registered_only=False):
    def stage(action, name, phase):
        milestone = f"{name}-{phase}"
        marker = RESULTS/name/(phase+".json")
        if not marker.exists() or (name == "timing" and not (RESULTS/"budget.json").exists()):
            arguments=[action,"--run",name]
            if phase == "final":
                arguments.append("--final")
            worker(*arguments)
        if public:
            if not (STATE/"publication"/(milestone+".json")).is_file():
                worker("publish","--milestone",milestone,"--run",name)
        elif not (STATE/"local-milestones"/(milestone+".json")).exists():
            worker("report")
            write_json(STATE/"local-milestones"/(milestone+".json"), {"time":stamp()})

    def fitted_replays(phase):
        for route in ROUTES:
            milestone=f"stack-{route}-{phase}"
            if not (RESULTS/"matched-depth"/f"{route}-{phase}.json").exists():
                worker("stack-replay","--route",route,*(("--final",) if phase=="final" else ()))
            if public and not (STATE/"publication"/(milestone+".json")).exists():
                worker("publish","--milestone",milestone)
            elif not public:
                worker("report")

    with study_lock("campaign"):
        if public:
            if not (STATE/"publication/protocol.json").exists():
                worker("publish","--milestone","protocol")
        stage("evaluate","base","development")
        if TRACK == "original":
            stage("train","timing","trained")
            if not registered_only:
                # Preserve the first preregistered solver, then test learnability before scaling.
                stage("train","d3-17","trained")
                stage("evaluate","d3-17","development")
                learnability_campaign(public)
                from .benchmark import freeze_profile
                freeze_profile(ORIGINAL_RESULTS)
                command = [sys.executable, "-u", "-m", "study.cli", "campaign"]
                if public:
                    command.append("--publish")
                subprocess.run(command, env={**os.environ, "STUDY_TRACK":"calibrated"}, check=True)
                return
        for run in matrix():
            stage("train",run.name,"trained")
            stage("evaluate",run.name,"development")
            if TRACK=="calibrated" and run.name=="alt-top-j3":
                # The supplemental arms reuse trained judges and the unchanged original solver schedule.
                fitted_replays("development")
                for extra in matched_runs(active_profile()):
                    stage("train",extra.name,"trained")
                    stage("evaluate",extra.name,"development")
        if not (RESULTS/"seal.json").exists() or (TRACK=="calibrated" and not (RESULTS/"matched-depth/seal.json").exists()):
            worker("seal")
        if public:
            worker("publish","--milestone","sealed-checkpoints")
        for name in ("base", *(r.name for r in matrix())):
            stage("evaluate",name,"final")
        if TRACK=="calibrated":
            fitted_replays("final")
            for extra in matched_runs(active_profile()):
                stage("evaluate",extra.name,"final")
        write_json(RESULTS/"completed.json",{"time":stamp(),"arms":len(matrix()),"matched_depth_arms":len(matched_runs(active_profile()))})
        if public:
            worker("publish","--milestone","complete")
        else:
            worker("report")


def dashboard(port):
    from .report import collect
    from .online_logs import serve_transcript
    transcripts = {f"/live/training-log/{name[-1]}":name for name in ONLINE_NAMES}
    class Handler(SimpleHTTPRequestHandler):
        def do_GET(self):
            path = self.path.split("?")[0]
            if path in transcripts:
                serve_transcript(self, transcripts[path])
            elif path == "/live.json":
                payload=json.dumps(collect(),ensure_ascii=False,allow_nan=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type","application/json; charset=utf-8")
                self.send_header("Cache-Control","no-store")
                self.send_header("Content-Length",str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
            else:
                super().do_GET()
    server=ThreadingHTTPServer(("127.0.0.1",port),partial(Handler,directory=str(ROOT/"docs")))
    print(f"Live study dashboard http://127.0.0.1:{port}/",flush=True)
    server.serve_forever()


def learnability_campaign(public):
    """Keep calibration and positive controls on the same local GPU in a fixed order."""
    root=RESULTS/"learnability"
    def milestone(action,name,marker,run=None,arguments=()):
        if not marker.is_file():
            worker(*action,*arguments)
        if public:
            worker("publish","--milestone",name,*(("--run",run) if run else ()))
        else:
            worker("report")

    with study_lock("learnability-campaign"):
        for phase in ("screen","confirm","audit"):
            marker=root/(phase+".json")
            milestone(("learnability",phase),"learnability-"+phase,marker)
            if phase=="screen" and not read_json(marker)["selected"]:
                return
            if phase=="confirm" and not read_json(marker)["confirmed"]:
                return
        for name in ("base",*PILOTS):
            if name in PILOTS:
                milestone(("train",),name+"-trained",RESULTS/name/"trained.json",name,("--run",name))
            milestone(("learnability","evaluate"),"learnability-"+name+"-evaluation",
                      root/"evaluations"/(name+".json"),arguments=("--run",name))
        milestone(("learnability","compare"),"learnability-outcome",root/"learning.json")


def main():
    parser=argparse.ArgumentParser(prog="study",description=__doc__)
    actions=parser.add_subparsers(dest="action",required=True)
    schedule=actions.add_parser("campaign")
    schedule.add_argument("--publish",action="store_true")
    frozen=actions.add_parser("frozen-judges",help="Run the GPU-only cross-model screen and independent confirmation")
    frozen.add_argument("--publish",action="store_true")
    online=actions.add_parser("online-solvers",help="Train fresh solvers with the independently confirmed frozen J2 and J3")
    online.add_argument("--publish",action="store_true")
    from .solver_fit import CANDIDATES
    fit=actions.add_parser("solver-fit",help="Measure less-quantized and pretraining-only solvers on the study GPU")
    fit.add_argument("--candidate",choices=CANDIDATES)
    fit.add_argument("--publish",action="store_true")
    schedule.add_argument("--registered-only", action="store_true",
                          help="Reproduce the original signed-arithmetic matrix independently")
    names=[*(r.name for r in matrix({})),*MATCHED_NAMES,*ONLINE_NAMES]
    actions.add_parser("train").add_argument("--run",required=True,choices=["timing",*PILOTS,*names])
    calibration=actions.add_parser("learnability",description="Calibrate arithmetic and test actual solver improvement")
    calibration.add_argument("phase",choices=["screen","confirm","audit","evaluate","compare","campaign"])
    calibration.add_argument("--run",choices=["base",*PILOTS],default="base")
    calibration.add_argument("--publish",action="store_true")
    evaluate=actions.add_parser("evaluate")
    evaluate.add_argument("--run",required=True,choices=["base",*names])
    evaluate.add_argument("--final",action="store_true")
    stacks=actions.add_parser("stack-replay",description="Measure each fitted judge depth on fixed base-solver answers")
    stacks.add_argument("--route",choices=ROUTES,required=True)
    stacks.add_argument("--final",action="store_true")
    actions.add_parser("seal")
    actions.add_parser("report")
    actions.add_parser("dashboard").add_argument("--port",default=8765,type=int)
    pub=actions.add_parser("publish")
    pub.add_argument("--milestone",required=True)
    pub.add_argument("--run")
    args=parser.parse_args()
    if args.action == "solver-fit":
        from .solver_fit import fit_candidates,probe
        if TRACK!="original":
            parser.error("Use the original results root for hardware probes")
        if args.candidate:
            with study_lock("fit-"+args.candidate):
                print(json.dumps(probe(args.candidate)),flush=True)
        else:
            fit_candidates(args.publish)
    elif args.action == "online-solvers":
        from .online_solvers import campaign as online_campaign
        online_campaign(args.publish)
    elif args.action in ("train","evaluate") and args.run in ONLINE_NAMES:
        from .online_solvers import evaluate_online, train_online
        if getattr(args,"final",False):
            parser.error("The online frozen-judge extension evaluates development questions only")
        with study_lock(args.action+"-"+args.run):
            (train_online if args.action=="train" else evaluate_online)(args.run)
    elif args.action == "frozen-judges":
        from .frozen_suite import campaign as frozen_campaign
        print(json.dumps(frozen_campaign(args.publish),ensure_ascii=False),flush=True)
    elif args.action == "campaign":
        if TRACK == "calibrated":
            from .benchmark import freeze_profile
            freeze_profile(ORIGINAL_RESULTS)
        campaign(args.publish, args.registered_only)
    elif TRACK == "calibrated" and (args.action=="learnability" or
                                    args.action=="train" and args.run in ("timing", *PILOTS)):
        parser.error("The disposable timing and learnability probes belong to the original results root")
    elif args.action == "train":
        from .training import train
        spec=run_spec(args.run)
        for dep in spec.dependencies:
            if not (RESULTS/dep/"trained.json").is_file():
                parser.error(f"Required checkpoint is missing: {dep}")
        budget=read_json(RESULTS/"budget.json")
        if args.run not in ("timing",*PILOTS) and not budget:
            parser.error("Run the registered timing pilot first.")
        with study_lock("train-"+args.run):
            train(spec,4 if args.run=="timing" else 128 if args.run in PILOTS else budget["updates"])
    elif args.action=="learnability":
        if args.phase=="campaign":
            learnability_campaign(args.publish)
        else:
            from . import learnability
            actions={"screen":learnability.screen,"confirm":learnability.confirm,"audit":learnability.audit,
                     "evaluate":lambda:learnability.evaluate_pilot(args.run),"compare":learnability.compare}
            with study_lock("learnability-"+args.phase+"-"+args.run):
                result=actions[args.phase]()
            print(json.dumps({k:v for k,v in result.items() if k!="usage"},ensure_ascii=False),flush=True)
    elif args.action == "evaluate":
        from .evaluate import evaluate
        with study_lock("evaluate-"+args.run+("-final" if args.final else "-dev")):
            evaluate(args.run,args.final)
    elif args.action=="stack-replay":
        from .evaluate import stack_replay
        with study_lock(f"stack-{args.route}-{'final' if args.final else 'development'}"):
            stack_replay(args.route,args.final)
    elif args.action == "seal":
        from .evaluate import seal
        seal()
    elif args.action == "report":
        from .report import build
        print(build()["primary"])
    elif args.action == "publish":
        from .publish import publish
        publish(args.milestone,args.run)
    elif args.action == "dashboard":
        dashboard(args.port)


if __name__=="__main__":
    main()
