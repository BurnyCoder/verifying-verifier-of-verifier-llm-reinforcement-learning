"""Verify precision-trial selection, denominator reporting and the within-group reward counterfactual."""

import pytest

from study import cli, solver_fit
from study.online_report import fit_results, fit_table, signal
from study.storage import write_json


@pytest.mark.parametrize("bf16_fits", [True,False])
def test_real_step_gate_selects_int8_only_on_bf16_fit_failure(tmp_path, monkeypatch, bf16_fits):
    observed = []
    def worker(action,*args):
        if action=="report":
            return
        assert action=="solver-fit" and args[0]=="--candidate"
        key=args[1]
        observed.append(key)
        name,_,dtype=solver_fit.CANDIDATES[key]
        ok=key!="original-bf16" or bf16_fits
        receipt=dict(model=name,precision=dtype,status="One update completed" if ok else "GPU fit unavailable")
        if ok:
            receipt.update(n=16,correct=0,parsed=2,after_step={"solver_peak_mib":1024})
        write_json(tmp_path/"solver-fit"/key/"result.json",receipt)
    monkeypatch.setattr(cli,"STATE",tmp_path/"state")
    monkeypatch.setattr(cli,"worker",worker)
    monkeypatch.setattr(solver_fit,"ORIGINAL_RESULTS",tmp_path)
    solver_fit.fit_candidates(False)
    assert observed == ["original-nf4","original-bf16",*([] if bf16_fits else ["original-int8"]),"base-2b"]
    _,data=fit_table(fit_results(tmp_path/"solver-fit"))
    assert data[0][4]=="0/16" and (data[1][4]=="—") == (not bf16_fits)


def test_all_approve_versus_all_reject_has_zero_centered_advantage():
    def rollout(step,j2,j3):
        return dict(step=step,label=0,reward=j3,reports=["0,1,7",f"1,0,7,{j2},0,7",f"1,0,7,{j3},0,7"])
    data = [rollout(0,0,1) for _ in range(4)] + [rollout(1,0,bit) for bit in (0,0,0,1)]
    s = signal(data)
    assert (s["groups"],s["j3_harmed"],s["changed_advantage_groups"],s["mixed"])==(2,5,1,1)
