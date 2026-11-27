"""Use artificial inputs and responses to check the normal frozen-judge scoring and resume paths."""

import pytest

from study.domain import Problem
from study.frozen_cases import CaseRunner, metrics, paired_confirmation
from study.frozen_gpu import LocalCUDA, verify_placement


class FixtureBackend:
    def __init__(self):
        self.calls = 0

    def generate(self, conversation):
        self.calls += 1
        # A constant answer earns some solution bits but cannot distinguish evidence twins.
        return {"text":"1,0,7,0,1,7", "input_tokens":20, "output_tokens":11,
                "elapsed_seconds":.01, "timings":{}, "finish_reason":"stop"}


def test_gpu_placement_rejects_partially_offloaded_or_cpu_weights():
    good = "offloaded 33/33 layers to GPU\nCUDA0 model buffer size = 1234.00 MiB\nCUDA0 KV buffer size = 24.00 MiB"
    assert verify_placement(good)["layers"] == 33
    for bad in (good.replace("33/33","32/33"), good.replace("CUDA0 KV", "CPU KV"),
                good+"\nCPU_Mapped model buffer size = 244.00 MiB"):
        with pytest.raises(ValueError):
            verify_placement(bad)


def test_template_prefill_never_becomes_a_judge_answer(monkeypatch, tmp_path):
    server = LocalCUDA(tmp_path/"weights",tmp_path/"log")
    rendered = "user question\n<|im_start|>assistant\n<think>\n\n</think>\n\n"
    def post(endpoint,payload):
        if endpoint=="/apply-template":
            assert payload["chat_template_kwargs"]["enable_thinking"] is False
            return {"prompt":rendered}
        assert endpoint=="/completion" and payload["prompt"]==rendered and payload["return_tokens"]
        return {"content":"0,1,7","tokens":[4,5,6],"tokens_evaluated":130,"tokens_predicted":3,
                "stop_type":"eos","timings":{"predicted_ms":10}}
    monkeypatch.setattr(server,"post",post)
    record = server.generate([{"role":"user","content":"user question"}])
    assert record["text"]=="0,1,7" and record["generated_token_ids"]==[4,5,6]
    assert record["rendered_prompt"]==rendered


def test_replay_preserves_twin_labels_and_resumes_identical_calls(tmp_path):
    p = Problem.from_expression("(4+3)*2")
    backend = FixtureBackend()
    runner = CaseRunner(tmp_path, backend, "fixture-weights", lambda *args,**kwargs: None)
    runner.balanced(p, 1)
    runner.twins(p, 1)
    before = backend.calls
    resumed = CaseRunner(tmp_path, backend, "fixture-weights", lambda *args,**kwargs: None)
    resumed.balanced(p,1)
    resumed.twins(p,1)
    scored = metrics(resumed.completed.values())
    assert backend.calls == before == 10
    assert scored["twins"]["visible"] == scored["twins"]["masked"] == 0
    assert scored["balanced"]["n"] == 2
    assert scored["balanced"]["depths"][2]["accuracy"] == .5
    assert scored["balanced"]["depths"][2]["full"] == 0
    assert paired_confirmation(resumed.completed,runner.completed)["twins"]["delta"] == 0
    with pytest.raises(ValueError):
        CaseRunner(tmp_path, backend, "different-weights", lambda *args,**kwargs: None)
