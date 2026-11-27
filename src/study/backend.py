"""One 4-bit checkpoint with a trainable policy adapter and read-only reward snapshots."""

import contextlib
import hashlib
import os
import time

import torch
from huggingface_hub import try_to_load_from_cache
from peft import LoraConfig, PeftModel, get_peft_model, prepare_model_for_kbit_training
from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

from .design import BASE, REVISION
from .prompts import messages
from .storage import adapter


def stream_seed(*parts):
    """Keep evaluator randomness independent of optimizer and rollout RNG streams."""
    digest = hashlib.sha256("|".join(map(str, parts)).encode()).digest()
    return int.from_bytes(digest[:4], "big")


class TokenStream:
    """Flush decoded output throughout generation and preserve a separate exact final transcript."""

    def __init__(self, backend):
        self.backend = backend
        self.first = True
        self.pending = []

    def put(self, ids):
        if self.first:
            self.first = False  # Transformers sends the whole input before its first generated token.
            return
        self.pending.append(ids.reshape(-1).cpu())
        if len(self.pending) == 8:
            self.flush()

    def flush(self):
        if self.pending:
            chunks = self.backend.tokenizer.batch_decode(torch.stack(self.pending, dim=1), skip_special_tokens=False)
            self.backend.journal.event("output_chunk", role=self.backend.label, text=chunks)
            self.pending.clear()

    def end(self):
        self.flush()


class Backend:
    def __init__(self, journal, initial=None, frozen=(), seed=17, *, model_id=BASE, revision=REVISION, precision="nf4", text_only=False):
        if not torch.cuda.is_available():
            raise RuntimeError("The registered GPU profile requires a CUDA device")
        torch.manual_seed(seed)
        self.journal, self.label = journal, "solver"
        # A complete immutable snapshot can be opened locally without repository discovery requests.
        weight_index = "model.safetensors.index.json" if text_only else "model.safetensors"
        required=("config.json",weight_index,"tokenizer.json","tokenizer_config.json")
        cached=all(isinstance(try_to_load_from_cache(model_id,filename,revision=revision),str) for filename in required)
        self.tokenizer = AutoTokenizer.from_pretrained(model_id, revision=revision, padding_side="left",local_files_only=cached)
        self.tokenizer.padding_side = "left"
        options = dict(dtype=torch.bfloat16, device_map={"":0}, attn_implementation="sdpa",local_files_only=cached)
        if precision == "nf4":
            options["quantization_config"] = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.bfloat16)
        elif precision == "int8":
            options["quantization_config"] = BitsAndBytesConfig(load_in_8bit=True)
        elif precision != "bf16":
            raise ValueError(f"Unknown solver precision {precision}")
        self.text_only = text_only
        if text_only:
            # Transformers maps the VLM checkpoint's language_model prefix to the text-only model.
            # https://huggingface.co/docs/transformers/model_doc/qwen3_5
            options["config"] = AutoConfig.from_pretrained(model_id, revision=revision, local_files_only=cached).get_text_config()
            options["output_loading_info"] = True
        loaded = AutoModelForCausalLM.from_pretrained(model_id, revision=revision, **options)
        if text_only:
            base, info = loaded
            if info["missing_keys"] or info["mismatched_keys"] or info["error_msgs"]:
                raise ValueError(f"Incomplete pretrained language weights: {info}")
        else:
            base = loaded
        if precision != "bf16":
            base = prepare_model_for_kbit_training(base, use_gradient_checkpointing=False)
        if initial:
            self.model = PeftModel.from_pretrained(base, adapter(initial), is_trainable=True)
        else:
            config = LoraConfig(r=16, lora_alpha=32, lora_dropout=0, task_type="CAUSAL_LM",
                                target_modules=["q_proj", "k_proj", "v_proj", "o_proj"])
            self.model = get_peft_model(base, config)
        self.names = {}
        for run in dict.fromkeys(r for r in frozen if r):
            name = "snapshot_" + str(len(self.names))
            self.model.load_adapter(adapter(run), adapter_name=name, is_trainable=False)
            self.names[run] = name
        self.model.set_adapter("default")
        self.totals = {}
        self._instrument()
        journal.event("hardware", device=torch.cuda.get_device_name(), capability=torch.cuda.get_device_capability(),
                      torch=torch.__version__, base=model_id, revision=revision, precision=precision, pid=os.getpid())

    def _instrument(self):
        """Record both TRL policy sampling and our explicit judge calls through generate()."""
        original = self.model.generate

        def generate(*args, **kwargs):
            ids = kwargs.get("input_ids", kwargs.get("inputs", args[0] if args else None))
            if ids is None:
                raise ValueError("Missing token IDs for logged generation")
            mask = kwargs.get("attention_mask")
            prompts = [self.tokenizer.decode(row if mask is None else row[mask[i].bool()], skip_special_tokens=False)
                       for i, row in enumerate(ids)]
            self.journal.event("prompts", role=self.label, text=prompts)
            event_start, event_end = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
            event_start.record()
            started = time.monotonic()
            kwargs.setdefault("streamer", TokenStream(self))
            result = original(*args, **kwargs)
            event_end.record()
            event_end.synchronize()
            seq = result.sequences if hasattr(result, "sequences") else result
            generated = seq[:, ids.shape[1]:]
            values = self.tokenizer.batch_decode(generated, skip_special_tokens=False)
            metrics = {"calls": len(seq), "input_tokens": int(mask.sum()) if mask is not None else ids.numel(),
                       "output_tokens": int((generated != self.tokenizer.pad_token_id).sum()),
                       "gpu_seconds": event_start.elapsed_time(event_end)/1000, "wall_seconds": time.monotonic()-started}
            totals = self.totals.setdefault(self.label, dict.fromkeys(metrics, 0))
            for k, v in metrics.items():
                totals[k] += v
            self.journal.event("outputs", role=self.label, text=values, **metrics)
            return result

        self.model.generate = generate

    def prompt(self, role, problem, trace="", history=()):
        kwargs = {"enable_thinking":False} if getattr(self,"text_only",False) else {}
        return self.tokenizer.apply_chat_template(messages(role, problem, trace, history,style=getattr(self,"prompt_style","registered")), tokenize=False,
                                                  add_generation_prompt=True, **kwargs)

    @contextlib.contextmanager
    def inference(self, snapshot, label, seed):
        """Restore training-mode, active adapter and RNG after every independent reward call."""
        old_label, training = self.label, self.model.training
        self.label = label
        previous = self.model.active_adapter
        previous = previous[0] if isinstance(previous, list) else previous
        try:
            self.model.eval()
            if snapshot:
                chosen = "default" if snapshot == "@active" else self.names[snapshot]
                self.model.set_adapter(chosen, inference_mode=True)
            scope = contextlib.nullcontext() if snapshot else self.model.disable_adapter()
            with scope, torch.no_grad(), torch.random.fork_rng(devices=[0]):
                torch.manual_seed(seed)
                yield
        finally:
            self.model.set_adapter(previous)
            self.model.train(training)
            self.label = old_label

    def generate(self, prompts, snapshot, label, seed, sample):
        with self.inference(snapshot, label, seed):
            encoded = self.tokenizer(prompts, padding=True, add_special_tokens=False, return_tensors="pt").to("cuda")
            parameters = dict(max_new_tokens=48, do_sample=sample, use_cache=True, top_k=0, top_p=1.0,
                              temperature=0.8 if sample else 1.0, pad_token_id=self.tokenizer.pad_token_id)
            tokens = self.model.generate(**encoded, **parameters)
            return self.tokenizer.batch_decode(tokens[:, encoded.input_ids.shape[1]:], skip_special_tokens=True)
