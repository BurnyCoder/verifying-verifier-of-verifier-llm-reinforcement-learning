"""Fully GPU-resident local GGUF judging using the pinned llama.cpp server and its placement log."""

import hashlib
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import time
import shutil
from urllib.error import URLError
from urllib.request import Request, urlopen

from .storage import ORIGINAL_STATE


BUILD = "b12807"
LIMIT = 48
CONTEXT = 2048


class GPUFitError(ValueError):
    """The model failed the measured CUDA placement or allocation check."""


def verify_placement(log):
    """Require every layer, all nonempty weight buffers and all KV/state buffers to be on CUDA."""
    layer = re.search(r"offloaded (\d+)/(\d+) layers to GPU",log,re.I)
    weights = re.findall(r"(\S+)\s+model buffer size\s*=\s*([\d.]+) MiB",log,re.I)
    caches = re.findall(r"(\S+)\s+(?:KV|RS|state) buffer size\s*=\s*([\d.]+) MiB",log,re.I)
    if not layer or int(layer[1])==0 or layer[1]!=layer[2]:
        raise GPUFitError("Incomplete CUDA layer placement")
    for label,buffers in (("weights",weights),("KV/state",caches)):
        if not buffers or any(device!="CUDA0" and float(size)>0 for device,size in buffers):
            raise GPUFitError(f"Unverified full CUDA {label} placement: {buffers}")
    if re.search(r"## SPLIT #\d+: CPU\b",log):
        raise GPUFitError("Dry inference graph contains a CPU compute split")
    return dict(layers=int(layer[1]),weights_mib=sum(float(s) for _,s in weights),
                cache_mib=sum(float(s) for _,s in caches),device="CUDA0")


def artifact_cache():
    return Path(os.environ.get("STUDY_FROZEN_DIR", ORIGINAL_STATE.parent/"frozen"))


def weight_file(model):
    """Check exact bytes before the runtime sees a model. Downloader resumes interrupted transfers."""
    from huggingface_hub import hf_hub_download
    directory = artifact_cache()/model.key
    path = directory/model.filename
    if model.repository.startswith("ollama/"):
        blob = Path(os.environ.get("OLLAMA_MODELS",Path.home()/".ollama/models"))/"blobs"/("sha256-"+model.sha256)
        if blob.is_file():
            path = blob
        elif not path.is_file():
            directory.mkdir(parents=True,exist_ok=True)
            partial = path.with_suffix(".partial")
            with urlopen("https://registry.ollama.ai/v2/library/qwen3.5/blobs/sha256:"+model.sha256,timeout=180) as src, partial.open("wb") as out:
                shutil.copyfileobj(src,out,length=1024*1024)
            partial.replace(path)
    elif not path.is_file():
        path = Path(hf_hub_download(model.repository,model.filename,revision=model.revision,local_dir=directory))
    with path.open("rb") as f:
        if path.stat().st_size != model.size or hashlib.file_digest(f,"sha256").hexdigest()!=model.sha256:
            raise RuntimeError(f"Weight artifact does not match the pinned digest: {model.filename}")
    return path


def device_memory():
    line = subprocess.check_output(["nvidia-smi","--query-gpu=name,memory.total,memory.free",
                                    "--format=csv,noheader,nounits","--id=0"],text=True).strip()
    name,total,free = line.rsplit(",",2)
    return dict(device=name.strip(),total_mib=int(total),free_mib=int(free))


class LocalCUDA:
    def __init__(self, path, log_path, template=None):
        self.path, self.log_path = path, log_path
        self.template = template
        self.process = None

    def __enter__(self):
        exe = Path(os.environ.get("STUDY_LLAMA_SERVER", artifact_cache()/BUILD/("llama-server.exe" if os.name=="nt" else "llama-server")))
        if not exe.is_file():
            raise FileNotFoundError(f"Set STUDY_LLAMA_SERVER to the {BUILD} CUDA server executable")
        # A fresh loopback port avoids an unrelated server receiving an experiment prompt.
        with socket.socket() as sock:
            sock.bind(("127.0.0.1",0))
            port = sock.getsockname()[1]
        self.url = f"http://127.0.0.1:{port}"
        self.log_path.parent.mkdir(parents=True,exist_ok=True)
        command = [str(exe),"-m",str(self.path),"--alias","judge","--host","127.0.0.1","--port",str(port),
                   "--device","CUDA0","-ngl","all","--fit","off","-ot",".*=CUDA0","--no-host","--op-offload",
                   "--backend-sampling","--no-warmup","-fa","on","-c",str(CONTEXT),"-np","1","-b","128","-ub","64",
                   "--cache-ram","0","--jinja","--no-mmproj","--verbosity","5","--chat-template-kwargs",'{"enable_thinking":false}']
        if self.template:
            command.extend(["--chat-template-file",str(self.template)])
        self.before = device_memory()
        start = time.monotonic()
        self.stream = self.log_path.open("wb")
        try:
            self.process = subprocess.Popen(command,stdout=self.stream,stderr=subprocess.STDOUT,
                cwd=exe.parent,env={**os.environ,"CUDA_VISIBLE_DEVICES":"0","GGML_SCHED_DEBUG":"1"},
                creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
            while time.monotonic()-start < 240:
                if self.process.poll() is not None:
                    log = self.log_path.read_text(encoding="utf-8",errors="replace")
                    if re.search(r"out of memory|failed to allocate|CUDA_ERROR_OUT_OF_MEMORY",log,re.I):
                        raise GPUFitError("CUDA allocation failed. "+log[-600:])
                    raise RuntimeError(f"llama-server exited {self.process.returncode}. {log[-1500:]}")
                try:
                    with urlopen(self.url+"/health",timeout=1) as response:
                        if json.load(response).get("status")=="ok":
                            break
                except (URLError,TimeoutError):
                    pass
                time.sleep(.25)
            else:
                raise TimeoutError("llama-server did not become ready within 240 seconds")
            log = self.log_path.read_text(encoding="utf-8",errors="replace")
            self.placement = dict(**verify_placement(log),before=self.before,after=device_memory(),
                                  load_seconds=time.monotonic()-start,build=BUILD,command=command)
            return self
        except BaseException:
            self.__exit__(None,None,None)
            raise

    def post(self, endpoint, payload):
        request = Request(self.url+endpoint,data=json.dumps(payload).encode(),
                          headers={"Content-Type":"application/json"})
        with urlopen(request,timeout=180) as response:
            return json.load(response)

    def generate(self, conversation):
        # /apply-template owns the native reasoning prefill. /completion returns generated tokens alone.
        # https://github.com/ggml-org/llama.cpp/blob/b12807/tools/server/README.md
        prompt = self.post("/apply-template",dict(messages=conversation,chat_template_kwargs={"enable_thinking":False}))["prompt"]
        if prompt.rstrip().endswith("<think>"):
            raise RuntimeError("The rendered template requested active reasoning")
        started = time.monotonic()
        result = self.post("/completion",dict(prompt=prompt,temperature=0,seed=17,n_predict=LIMIT,
                           cache_prompt=False,return_tokens=True,timings_per_token=True))
        return dict(text=result["content"],generated_token_ids=result["tokens"],rendered_prompt=prompt,
                    finish_reason=result["stop_type"],input_tokens=result["tokens_evaluated"],output_tokens=result["tokens_predicted"],
                    timings=result.get("timings",{}),elapsed_seconds=time.monotonic()-started)

    def __exit__(self, *exc):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
        self.stream.close()
