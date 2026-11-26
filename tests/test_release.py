"""Exercise the final report with artificial IDs, without opening any real held-out problem."""

import json
import os
import subprocess
import sys

from pypdf import PdfReader

from study.design import SEEDS, matrix
from study.storage import write_json


def test_full_release_from_synthetic_raw_records(tmp_path):
    results=tmp_path/"results"
    (tmp_path/"README.md").write_text("Fixture\n<!-- RESULTS:START -->\n<!-- RESULTS:END -->\n",encoding="utf-8")
    natural=dict(key="fixture-common",expression="(2+3)*4",problem=["s1 = 2 + 3","s2 = s1 * 4"],
                 trace="5,20",expected_values=[5,20],correct=1,final_correct=1,malformed=False,split="dev",
                 reports=["1,0,20","1,0,20,1,0,20","1,0,20,1,0,20"],votes=["1,0,20"]*3,verdicts=[1]*3,
                 flat=1,full_report_correct=[1]*3,judge_malformed=[False]*3,fixed=0,harmed=0)
    test_arms={f"{arm}-{seed}" for arm in ("d3","d2","flat") for seed in SEEDS}
    for spec in matrix():
        target=results/spec.name
        cost=dict(calls=4,input_tokens=20,output_tokens=16,gpu_seconds=.5)
        usage={"j3":cost} if spec.name=="d3-17" else {}
        write_json(target/"trained.json",{"updates":1,"elapsed_seconds":12,"usage":usage})
        write_json(target/"development.json",{"weights":"fixture"})
        write_json(target/"final.json",{"weights":"fixture"})
        (target/"replay.jsonl").write_text(json.dumps(natural)+"\n",encoding="utf-8")
        if spec.name=="d3-17":
            group=[dict(step=0,sample=i,reward=int(i<2),label=int(i<1)) for i in range(4)]
            (target/"rollouts.jsonl").write_text("".join(json.dumps(r)+"\n" for r in group),encoding="utf-8")
            (target/"metrics.jsonl").write_text('{"step":1,"loss":0.0}\n',encoding="utf-8")
        if spec.role=="j3":
            case=dict(key="fixture-pair",expression="(2+3)*4",split="mechanism",trace="5,20",first="1,0,20",
                      reviews=["1,0,20,1,0,20","1,0,19,1,0,20"],labels=[[1,0,20,1,0,20],[0,3,20,1,0,20]],
                      visible=["1,0,20,1,0,20","0,3,20,1,0,20"],masked=["bad","bad"],visible_pair=1,masked_pair=0)
            for name in ("mechanism","unseen-evidence","layout-evidence","transfer-evidence"):
                (target/(name+".jsonl")).write_text(json.dumps(case)+"\n",encoding="utf-8")
        if spec.name in test_arms:
            with (target/"test.jsonl").open("w",encoding="utf-8") as file:
                for i in range(2048):
                    passed=int(spec.reward=="d3" or (spec.reward=="flat" and i%2==0))
                    row=dict(key=f"fixture-{i}",correct=passed,final_correct=1,malformed=False,
                             trace="5,20" if passed else "6,20",expected_values=[5,20])
                    file.write(json.dumps(row)+"\n")
        elif spec.role.startswith("j"):
            (target/"judge-test.jsonl").write_text(json.dumps(natural)+"\n",encoding="utf-8")
    env=dict(os.environ,STUDY_RESULTS=str(results),STUDY_STATE=str(tmp_path/"checkpoints"),PYTHONUTF8="1")
    subprocess.run([sys.executable,"-m","study.cli","report"],cwd=tmp_path,env=env,check=True,capture_output=True)
    data=json.loads((tmp_path/"docs/assets/study.json").read_text(encoding="utf-8"))
    assert data["primary"]["delta"]==1 and data["flat"]["delta"]==.5
    j1=next(r for r in data["runs"] if r["name"]=="exact-j1")
    assert (j1["test_n"],j1["test"])==(1,1)
    assert (tmp_path/"docs/assets/paired-outcomes.png").stat().st_size>1000
    assert (tmp_path/"docs/assets/training.png").stat().st_size>1000
    paper=PdfReader(tmp_path/"reports/paper.pdf")
    assert "AI statement" in paper.pages[-1].extract_text()
    assert "D3" in (tmp_path/"reports/summary.md").read_text(encoding="utf-8")
    # Regenerating from a second, empty results directory must not show the previous study's plots.
    env["STUDY_RESULTS"]=str(tmp_path/"empty-results")
    subprocess.run([sys.executable,"-m","study.cli","report"],cwd=tmp_path,env=env,check=True,capture_output=True)
    assert not (tmp_path/"docs/assets/paired-outcomes.png").exists()
    assert "outcomes.png" not in (tmp_path/"README.md").read_text(encoding="utf-8")


def test_learning_figure_contains_only_observed_conditions_and_is_removed_when_empty(tmp_path):
    from study.learnability_report import learning_figure

    chart = tmp_path / "learnability.png"
    trials = {"base":{"n":256,"correct":128}, "learn-oracle-17":{"n":256,"correct":192}, "learn-shuffle-17":None}
    learning_figure({"evaluations":trials, "learning":None},chart)
    assert chart.stat().st_size>1000
    trials["learn-shuffle-17"]={"n":256,"correct":128}
    change={"delta":.25, "interval":[.14,.36]}
    learning_figure({"evaluations":trials, "learning":{"over_base":change,"over_shuffled":change}},chart)
    assert chart.stat().st_size>1000
    learning_figure({"evaluations":{}, "learning":None},chart)
    assert not chart.exists()
