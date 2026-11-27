"""Use artificial inputs and responses to check the normal frozen-judge scoring and resume paths."""

import pytest

from study.domain import Problem
from study.frozen_cases import CaseRunner, metrics, paired_confirmation
from study.frozen_gpu import GPUFitError, LocalCUDA, require_dedicated_memory, verify_placement


class FixtureBackend:
    def __init__(self):
        self.calls = 0

    def generate(self, conversation):
        self.calls += 1
        # A constant answer earns some solution bits but cannot distinguish evidence twins.
        return {"text":"1,0,7,0,1,7", "input_tokens":20, "output_tokens":11,
                "generated_token_ids":[1,2], "rendered_prompt":str(conversation),
                "elapsed_seconds":.01, "timings":{}, "finish_reason":"stop"}


def test_gpu_placement_rejects_partially_offloaded_or_cpu_weights():
    good = "offloaded 33/33 layers to GPU\nCUDA0 model buffer size = 1234.00 MiB\nCUDA0 KV buffer size = 24.00 MiB"
    assert verify_placement(good)["layers"] == 33
    for bad in (good.replace("33/33","32/33"), good.replace("CUDA0 KV", "CPU KV"),
                good+"\nCPU_Mapped model buffer size = 244.00 MiB"):
        with pytest.raises(ValueError):
            verify_placement(bad)


def test_native_graph_log_checks_scheduled_devices_and_rejects_host_compute(tmp_path):
    from study.frozen_device import graph_assignments
    log=tmp_path/"server.log"
    log.write_text("## SPLIT #0: CUDA0 # 4 inputs\n## SPLIT #1: CUDA0 # 1 inputs\n")
    assert graph_assignments(log)["graph_assignments"]=={"CUDA0":2}
    with log.open("a") as f:
        f.write("## SPLIT #2: CPU # 3 inputs\n")
    with pytest.raises(ValueError,match="CPU-free computation"):
        graph_assignments(log)


def test_dedicated_gpu_allocation_must_cover_weights_and_cache():
    planned={"weights_mib":5200,"cache_mib":160}
    require_dedicated_memory(planned, 5370)
    with pytest.raises(GPUFitError,match="5100"):
        require_dedicated_memory(planned,5100)


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


def test_release_audit_detects_changed_evidence_even_when_verdict_totals_match(tmp_path):
    import json
    from study.frozen_audit import audit
    from study.storage import atomic, rows
    p = Problem.from_expression("(4+3)*2")
    r = CaseRunner(tmp_path,FixtureBackend(),"fixture",lambda *a,**kw:None)
    for i in range(4):
        r.ask(f"timing/{i}",1,p,"8,14",[])
    r.balanced(p,0)
    r.twins(p,0)
    receipt = dict(metrics=metrics(r.completed.values()),cost={"calls":10})
    assert audit(tmp_path,receipt)["matched_masked_outputs"]==1
    data=list(rows(tmp_path/"cases.jsonl"))
    data[-1]["visible"]["outputs"][1]="0,3,7,0,1,7"
    atomic(tmp_path/"cases.jsonl","".join(json.dumps(v)+"\n" for v in data))
    with pytest.raises(ValueError,match="Logged judge output"):
        audit(tmp_path,receipt)


def test_conversion_comparison_matches_twin_requests_by_identity(tmp_path):
    from study.frozen_report import compare_conversions
    from study.storage import append
    left, right = tmp_path / "primary.jsonl", tmp_path / "alternate.jsonl"
    observations = [dict(id=f"twins/example/visible/{i}", rendered_prompt=f"review {i}",
                         messages=[{"role":"user", "content":str(i)}], input_tokens=8, text="yes") for i in range(2)]
    for r in observations:
        append(left, r)
    append(right, {**observations[1], "text":"no"})
    append(right, observations[0])
    summary = compare_conversions(left, right)
    assert summary == dict(calls=2, same_messages=2, same_prompts=2, same_input_counts=2, same_outputs=1)
    append(right, {**observations[0], "id":"twins/unmatched/visible/0"})
    with pytest.raises(ValueError, match="identities"):
        compare_conversions(left, right)


def test_frozen_table_shows_offsetting_errors_when_depth_scores_tie():
    from study.frozen_report import HEAD, depth_rows
    measures = {"balanced": {"n":4, "depths":[{"correct":2}]*3, "fixed":1, "harmed":1},
                "natural":{"n":0}, "twins":{"n":2, "visible":1, "masked":0}}
    row, = depth_rows({"results":[{"model":"fixture", "phase":"screen", "metrics":measures}]})
    assert len(row) == len(HEAD)
    assert row[2:4] == ["2/4", "2/4"]
    assert row[-1] == "1 / 1"


def test_failed_gpu_fit_is_visible_before_any_model_answers(tmp_path):
    from study.frozen_report import collect_frozen, interpretation
    from study.storage import write_json
    write_json(tmp_path/"q38-27b/fit.json", [{"file":"larger.gguf", "fit":False, "reason":"Insufficient dedicated memory"}])
    data = collect_frozen(tmp_path)
    assert not data["results"]
    assert data["fit_failures"] == [{"key":"q38-27b", "file":"larger.gguf", "reason":"Insufficient dedicated memory"}]
    assert "larger.gguf" in " ".join(interpretation(data))


def test_gpu_engine_time_uses_physical_deltas_and_excludes_counter_resets():
    from study.frozen_device import measured_engine_times
    def sample(second,pid,counter):
        return {"time":f"2026-11-27T00:00:{second:02d}+00:00", "pid":pid,
                "engines":[{"engine":"3D","seconds":counter}]}
    observations = [sample(0,7,1), sample(5,7,3), sample(10,7,1e12), sample(15,7,1e12+4),
                    sample(20,7,1), sample(25,11,100), sample(30,11,104)]
    total, = measured_engine_times(observations)
    assert total == {"engine":"3D", "seconds":10, "interval_seconds":15, "usable":3, "discarded":2}


def test_sustained_latency_requires_a_measured_slow_call_after_reload():
    from study.frozen_latency import slow_segment
    fits = [{"fit":True,"file":"same.gguf","time":"00"}]
    calls = [{"id":f"fixed/{i}","time":f"0{i}","elapsed_seconds":40} for i in (1,2,3)]
    assert not slow_segment(calls,fits)['reloaded']
    fits.append({"fit":True,"file":"same.gguf","time":"04"})
    assert slow_segment(calls,fits) is None
    later = {"id":"fixed/5","time":"05","elapsed_seconds":41}
    report = slow_segment([*calls,later],fits)
    assert report['reloaded'] and len(report['evidence'])==4
    assert slow_segment([*calls,{**later,'elapsed_seconds':2}],fits) is None


def test_fresh_throughput_fallback_can_win_without_its_partial_predecessor(tmp_path,monkeypatch):
    from contextlib import nullcontext
    from study import cli, frozen_device, frozen_suite as suite
    from study.storage import write_json
    observed=[]
    def run(key,model,phase,confirmed_file=None):
        observed.append((key,model.key,confirmed_file))
        if key=='q38-27b':
            return dict(status='Incomplete, sustained latency',file='earlier.gguf')
        if key.startswith('confirm-'):
            write_json(tmp_path/key/'result.json',{'status':'Complete'})
        rate = {'q35-9b':1,'q35-4b':2,'q38-27b-iq1s':3}.get(key,0)
        return dict(status='Complete',file=confirmed_file or model.filename,cost={'elapsed_seconds':1},
                    metrics={'twins':{'visible':rate},'balanced':{'depths':[{}, {}, {'accuracy':.5}]}})
    monkeypatch.setattr(suite,'ROOT',tmp_path)
    monkeypatch.setattr(suite,'run_one',run)
    monkeypatch.setattr(suite,'paired_confirmation',lambda *args:{'twins':{'delta':0},'balanced_verdict':{'delta':0}})
    monkeypatch.setattr(cli,'study_lock',lambda name:nullcontext())
    monkeypatch.setattr(cli,'worker',lambda *args:None)
    monkeypatch.setattr(frozen_device,'close_device_records',lambda:None)
    decision=suite.campaign()
    assert decision['original_completed_selection']=='q35-4b' and decision['selected']=='q38-27b-iq1s'
    assert ('confirm-winner','q38-27b',suite.SMALLER_FILES['q38-27b'][-1][0]) in observed
    assert not decision['online_gate']
