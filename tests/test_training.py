"""Exercise the actual reward callback and freeze mechanics with a deterministic test double."""

from types import SimpleNamespace

import pytest


def test_reward_callback_routes_to_solution_and_teacher_bits(tmp_path, monkeypatch):
    training = pytest.importorskip("study.training")
    from study.design import Run
    from study.storage import rows

    class Fixture:
        journal = SimpleNamespace(event=lambda *args, **kwargs: None)
        def prompt(self, *args):
            return "public input"
        def generate(self, prompts, snapshot, label, seed, sample):
            return ["0,1,7" if label=="j1" else "1,0,7,0,1,7"]*len(prompts)
    monkeypatch.setattr(training,"RESULTS",tmp_path)
    inputs=dict(prompts=["p"]*4,completions=["8,14"]*4,expression=["(4+3)*2"]*4,trace=[""]*4,
                history_json=["[]"]*4,trainer_state=SimpleNamespace(global_step=0))
    for arm in ("d1","d2","d3","flat","oracle","hybrid","shuffle"):
        assert training.Reward(Fixture(),Run(arm,reward=arm))(**inputs)==[0]*4
    inputs.update(completions=["0,1,7"]*4,trace=["8,14"]*4)
    assert training.Reward(Fixture(),Run("teacher",role="j1",reward="teacher",teacher="snapshot"))(**inputs)==[1]*4
    entries=list(rows(tmp_path/"d3"/"rollouts.jsonl"))
    assert entries[0]["label"]==0 and len(entries[0]["reports"])==3


def test_lora_snapshot_and_rng_restored():
    torch=pytest.importorskip("torch")
    pytest.importorskip("peft")
    from peft import LoraConfig, get_peft_model
    from transformers import Qwen2Config, Qwen2ForCausalLM
    from study.backend import Backend
    from study.training import frozen_fingerprint
    if not torch.cuda.is_available():
        pytest.skip("CUDA RNG isolation requires the GPU profile")
    tiny=Qwen2ForCausalLM(Qwen2Config(vocab_size=64,hidden_size=32,intermediate_size=64,
                                      num_hidden_layers=1,num_attention_heads=4,num_key_value_heads=2))
    cfg=LoraConfig(r=2,lora_alpha=2,target_modules=["q_proj"],task_type="CAUSAL_LM")
    backend=Backend.__new__(Backend)
    backend.model=get_peft_model(tiny,cfg)
    backend.model.add_adapter("snapshot_0",cfg)
    backend.names={"frozen":"snapshot_0"}
    backend.label="solver"
    backend.model.set_adapter("default")
    digest=frozen_fingerprint(backend.model)
    rng=torch.get_rng_state().clone()
    gpu_rng=torch.cuda.get_rng_state().clone()
    with backend.inference("frozen","j3",29):
        torch.rand(3)
        torch.rand(3, device="cuda")
        assert not backend.model.training and backend.model.active_adapter=="snapshot_0"
    assert torch.equal(rng,torch.get_rng_state())
    assert torch.equal(gpu_rng,torch.cuda.get_rng_state())
    assert backend.model.training and backend.model.active_adapter=="default"
    assert digest==frozen_fingerprint(backend.model)
