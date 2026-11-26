"""Publish committed study artifacts and role adapters to the registered public repositories."""

import gzip
import shutil
import subprocess

from .design import GITHUB
from .storage import RESULTS, ROOT, STATE, adapter, read_json, stamp, write_json

DATA = "BurnyCoder/recursive-judge-grpo-study"
MODELS = "BurnyCoder/recursive-judge-grpo-adapters"


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True, encoding="utf-8").strip()


def publish(milestone, run=None):
    from huggingface_hub import CommitOperationAdd, HfApi
    from .report import build

    receipt = STATE/"publication"/(milestone+".json")
    if receipt.exists():
        return
    if RESULTS != (ROOT/"results").resolve():
        raise RuntimeError("Independent replication results use local reporting; the public release uses the registered results directory")
    build()
    if git("branch", "--show-current") != "main":
        raise RuntimeError("Publish experiment milestones from the merged main checkout")
    git("add", "--", "README.md", "results", "reports", "docs")
    if git("diff","--cached","--name-only"):
        git("commit","-m",f"Record {milestone} study milestone")
    git("push","origin","main")
    head = git("rev-parse","HEAD")
    api = HfApi()
    previous = read_json(STATE/"publication"/"latest.json", {})
    changed = (git("diff","--name-only","--diff-filter=ACMRT",previous["git"],head) if previous
               else git("ls-files"))
    paths = [p for p in changed.splitlines() if (ROOT/p).is_file() and p!=".env"]
    operations = [CommitOperationAdd(path_in_repo=p, path_or_fileobj=str(ROOT/p)) for p in paths if p!="README.md"]
    dataset_card = "---\npretty_name: Recursive judge evidence and GRPO outcomes\nviewer: false\n---\n" + (ROOT/"README.md").read_text(encoding="utf-8")
    operations.append(CommitOperationAdd(path_in_repo="README.md",path_or_fileobj=dataset_card.encode()))
    logdir = ROOT/"logs"/(milestone if not run else run)
    if milestone.endswith("-development") or milestone.endswith("-final"):
        logdir = ROOT/"logs"/milestone
    for path in sorted(logdir.glob("*.jsonl")):
        packed=STATE/"publication"/"compressed"/logdir.name/(path.name+".gz")
        packed.parent.mkdir(parents=True,exist_ok=True)
        with path.open("rb") as source, gzip.open(packed,"wb",compresslevel=5) as target:
            shutil.copyfileobj(source,target)
        operations.append(CommitOperationAdd(path_in_repo=f"logs/{logdir.name}/{packed.name}",path_or_fileobj=str(packed)))
    if operations:
        api.create_commit(repo_id=DATA,repo_type="dataset",operations=operations,commit_message=f"{milestone} · {head[:12]}")
    card = ("---\nbase_model: Qwen/Qwen2.5-1.5B-Instruct\nlibrary_name: peft\nlicense: apache-2.0\n---\n"
            "# Recursive judge GRPO adapters\n\nRole-specific Qwen adapters are stored under runs/RUN_ID. "
            "The base model revision is 989aa7980e4cf806f80c7fef2b1adb7bc71aa306. "
            f"[Study, run matrix and evaluation]({GITHUB}). "
            f"[Raw data, logs and paper](https://huggingface.co/datasets/{DATA}). "
            f"[Load an adapter]({GITHUB}/blob/main/docs/usage.md#using-a-published-adapter).\n\n"
            +(ROOT/"reports/summary.md").read_text(encoding="utf-8").replace("(preregistration.md)",f"({GITHUB}/blob/main/reports/preregistration.md)"))
    api.upload_file(path_or_fileobj=card.encode(),path_in_repo="README.md",repo_id=MODELS,
                    commit_message=f"Update study card at {milestone}")
    if run and (adapter(run)/"adapter_config.json").is_file() and milestone.endswith("-trained"):
        api.upload_folder(folder_path=str(adapter(run)), path_in_repo=f"runs/{run}",repo_id=MODELS,
                          commit_message=f"Publish {run} role adapter")
    marker={"git":head,"time":stamp(),"milestone":milestone}
    write_json(receipt,marker)
    write_json(STATE/"publication"/"latest.json",marker)
