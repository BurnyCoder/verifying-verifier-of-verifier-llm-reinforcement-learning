"""Verify interruption and optimizer/RNG recovery through the ordinary train CLI on a tiny CPU model."""

import sys

import pytest


def test_normal_train_entry_resumes_at_complete_grpo_group(tmp_path, monkeypatch):
    tr = pytest.importorskip("study.training")
    import torch
    from peft import LoraConfig, get_peft_model
    from tokenizers import Tokenizer
    from tokenizers.models import WordLevel
    from tokenizers.pre_tokenizers import Whitespace
    from transformers import PreTrainedTokenizerFast, Qwen2Config, Qwen2ForCausalLM
    from study import cli, storage

    class TinyBackend:
        """Only model construction and frozen reward generation are replaced in this fixture."""
        def __init__(self, journal, initial, frozen, seed):
            torch.manual_seed(seed)
            tokens = ["<pad>", "<unk>", "<eos>", "compute", "0", "1", "2", "3"]
            vocab = {t: i for i,t in enumerate(tokens)}
            tokenizer = Tokenizer(WordLevel(vocab, unk_token="<unk>"))
            tokenizer.pre_tokenizer = Whitespace()
            self.tokenizer = PreTrainedTokenizerFast(tokenizer_object=tokenizer, pad_token="<pad>",
                                                     eos_token="<eos>", unk_token="<unk>", padding_side="left")
            model = Qwen2ForCausalLM(Qwen2Config(vocab_size=len(tokens),hidden_size=16,intermediate_size=32,
                num_hidden_layers=1,num_attention_heads=2,num_key_value_heads=1,pad_token_id=0,eos_token_id=2))
            self.model = get_peft_model(model,LoraConfig(r=2,lora_alpha=2,target_modules=["q_proj"],task_type="CAUSAL_LM"))
            self.journal, self.totals = journal, {}

        def prompt(self, *args):
            return "compute"

        def generate(self, prompts, snapshot, label, seed, sample):
            # The two reward classes guarantee that the small test exercises a gradient update.
            return [("1,0,5" if i%2 else "0,1,5") if label=="j1"
                    else ("1,0,5,1,0,5" if i%2 else "1,0,5,0,1,5") for i in range(len(prompts))]

    original_config = tr.GRPOConfig
    def cpu_config(**options):
        options.update(use_cpu=True,bf16=False,gradient_checkpointing=False,max_completion_length=4,
                       gradient_checkpointing_kwargs=None,save_steps=1,dataloader_pin_memory=False)
        return original_config(**options)

    monkeypatch.setattr(tr,"Backend",TinyBackend)
    monkeypatch.setattr(tr,"GRPOConfig",cpu_config)
    monkeypatch.setattr(sys,"argv",["study","train","--run","d3-17"])
    torch.set_num_threads(1)

    def location(name):
        root=tmp_path/name
        monkeypatch.setattr(storage,"ROOT",root)
        for module in (storage,cli,tr):
            monkeypatch.setattr(module,"STATE",root/"state")
            monkeypatch.setattr(module,"RESULTS",root/"results")
        storage.write_json(root/"results/budget.json",{"updates":2})
        return root

    interrupted=location("interrupted")
    once=[True]
    original_save=tr.Metrics.on_save
    def interrupt(self,args,state,control,**kwargs):
        if once[0] and state.global_step==1:
            once[0]=False
            raise InterruptedError("Planned test interruption after a real optimizer checkpoint")
        return original_save(self,args,state,control,**kwargs)
    monkeypatch.setattr(tr.Metrics,"on_save",interrupt)
    with pytest.raises(InterruptedError):
        cli.main()
    assert (interrupted/"state/runs/d3-17/trainer/checkpoint-1/optimizer.pt").exists()
    # Simulate the OS stopping inside the subsequent save, before Trainer finishes its commit record.
    torn = interrupted/"state/runs/d3-17/trainer/checkpoint-2"
    torn.mkdir()
    (torn/"trainer_state.json").write_text('{"global_step":', encoding="utf-8")
    storage.append(interrupted/"results/d3-17/rollouts.jsonl",{"step":1,"sample":99})
    cli.main()
    result=storage.read_json(interrupted/"results/d3-17/trained.json")
    assert result["updates"]==2 and result["resumed_at"]==1

    baseline=location("continuous")
    cli.main()
    from safetensors.torch import load_file
    def observations(root):
        return [(r["step"],r["sample"],r["key"],r["answer"],r["reward"])
                for r in storage.rows(root/"results/d3-17/rollouts.jsonl")]
    assert len(observations(interrupted))==8
    assert observations(interrupted)==observations(baseline)
    left=load_file(interrupted/"state/runs/d3-17/adapter/adapter_model.safetensors")
    right=load_file(baseline/"state/runs/d3-17/adapter/adapter_model.safetensors")
    assert left.keys()==right.keys() and all(torch.equal(left[k],right[k]) for k in left)
