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

from .design import Run, matrix
from .storage import RESULTS, ROOT, STATE, read_json, stamp, write_json


def run_spec(name):
    if name == "timing":
        return Run("timing")
    return next(row for row in matrix() if row.name == name)


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
    with (STATE/(name+".lock")).open("a+b") as lock:
        lock.seek(0)
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        else:
            import fcntl
            fcntl.flock(lock,fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def campaign(public):
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

    with study_lock("campaign"):
        if public:
            if not (STATE/"publication/protocol.json").exists():
                worker("publish","--milestone","protocol")
        stage("evaluate","base","development")
        stage("train","timing","trained")
        for run in matrix():
            stage("train",run.name,"trained")
            stage("evaluate",run.name,"development")
        if not (RESULTS/"seal.json").exists():
            worker("seal")
        if public:
            worker("publish","--milestone","sealed-checkpoints")
        for name in ("base", *(r.name for r in matrix())):
            stage("evaluate",name,"final")
        write_json(RESULTS/"completed.json",{"time":stamp(),"arms":len(matrix())})
        if public:
            worker("publish","--milestone","complete")
        else:
            worker("report")


def dashboard(port):
    from .report import collect
    class Handler(SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path.split("?")[0] == "/live.json":
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


def main():
    parser=argparse.ArgumentParser(prog="study",description=__doc__)
    actions=parser.add_subparsers(dest="action",required=True)
    schedule=actions.add_parser("campaign")
    schedule.add_argument("--publish",action="store_true")
    names=[r.name for r in matrix()]
    actions.add_parser("train").add_argument("--run",required=True,choices=["timing",*names])
    evaluate=actions.add_parser("evaluate")
    evaluate.add_argument("--run",required=True,choices=["base",*names])
    evaluate.add_argument("--final",action="store_true")
    actions.add_parser("seal")
    actions.add_parser("report")
    actions.add_parser("dashboard").add_argument("--port",default=8765,type=int)
    pub=actions.add_parser("publish")
    pub.add_argument("--milestone",required=True)
    pub.add_argument("--run")
    args=parser.parse_args()
    if args.action == "campaign":
        campaign(args.publish)
    elif args.action == "train":
        from .training import train
        spec=run_spec(args.run)
        for dep in spec.dependencies:
            if not (RESULTS/dep/"trained.json").is_file():
                parser.error(f"Required checkpoint is missing: {dep}")
        budget=read_json(RESULTS/"budget.json")
        if args.run!="timing" and not budget:
            parser.error("Run the registered timing pilot first.")
        with study_lock("train-"+args.run):
            train(spec,4 if args.run=="timing" else budget["updates"])
    elif args.action == "evaluate":
        from .evaluate import evaluate
        with study_lock("evaluate-"+args.run+("-final" if args.final else "-dev")):
            evaluate(args.run,args.final)
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
