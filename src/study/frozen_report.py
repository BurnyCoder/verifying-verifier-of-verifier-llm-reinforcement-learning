"""Use the completed fixed-trace receipts for side-by-side depth and evidence results."""

from functools import lru_cache

from .frozen_audit import audit
from .frozen_models import LOCAL_REPLICATES, MODELS
from .storage import atomic, read_json, rows
from .tables import markdown


HEAD = ["Model and cohort","J1 verdict","J2 verdict","J3 verdict","J3 visible pairs","J3 masked pairs"]


@lru_cache(maxsize=16)
def released_audit(folder, receipt_time):
    """A completed receipt identifies immutable calls. Avoid re-reading them on every dashboard refresh."""
    return audit(folder, read_json(folder/"result.json"))


def collect_frozen(root):
    results = []
    for key in ("runtime-format-pilot",*[model.key for model in (*LOCAL_REPLICATES,*MODELS)],"confirm-control","confirm-winner"):
        receipt = read_json(root/key/"result.json",{})
        if receipt:
            if receipt.get("metrics"):
                receipt["audit"] = released_audit(root/key,receipt["time"])
                samples = list(rows(root/key/"gpu-telemetry.jsonl"))
                if samples:
                    receipt["gpu"] = dict(peak_dedicated_mib=max(r["dedicated_bytes"] for r in samples)/2**20,
                                          engines=samples[-1]["engines"],last_sample=samples[-1]["time"])
            results.append({**receipt,"key":key})
    return dict(results=results,decision=read_json(root/"decision.json",{}))


def depth_rows(study):
    for result in study["results"]:
        measure = result.get("metrics")
        if not measure:
            continue
        for cohort in ("balanced","natural"):
            record = measure[cohort]
            if not record["n"]:
                continue
            twins = measure["twins"]
            values = [f"{d['correct']}/{record['n']}" for d in record["depths"]]
            pairs = [f"{twins[c]}/{twins['n']}" if cohort=="balanced" else "—" for c in ("visible","masked")]
            yield [f"{result['model']} · {result['phase']} · {cohort}", *values, *pairs]


def frozen_text(study):
    records = list(depth_rows(study))
    parts = ["## Newer frozen judges on fixed solver answers"]
    if records:
        parts += ["Every depth grades the same solver responses within a cohort. A visible-pair success requires both complete audit records and the exact numerical correction. Each balanced problem contributes one valid trace and one invalid trace.",markdown(HEAD,records)]
    else:
        parts.append("No completed fixed-trace score has been released.")
    for r in study["results"]:
        if r.get("metrics"):
            m = r["metrics"]["natural"]
            costs = r["cost"]
            parts.append(f"{r['model']} ({r['phase']}, {r['file']}) used {costs['input_tokens']:,} input and {costs['output_tokens']:,} output tokens in {costs['elapsed_seconds']:.1f} seconds of end-to-end calls."+
                         (f" On the {m['n']} natural traces, Judge 3 fixed {m['fixed']} verdicts and introduced {m['harmed']} errors." if m["n"] else ""))
        else:
            parts.append(f"{r['model']} · {r['status']}. {r['result']}.")
    decision = study["decision"]
    if decision:
        parts.append(decision["result"]+".")
        for metric, estimate in decision.get("estimates",{}).items():
            lo,hi = estimate["ci"]
            parts.append(f"{metric.replace('_',' ')} improved by a signed {estimate['delta']*100:+.2f} percentage points on {estimate['n']} paired problems (95% interval {100*lo:+.2f} to {100*hi:+.2f}).")
    return "\n\n".join(parts)


def plot_scores(study, path):
    """Keep distinct denominators visible even when the fraction correct shares a common color scale."""
    import matplotlib.pyplot as plt
    import numpy as np
    selected=[r for r in study["results"] if r.get("metrics")]
    if not selected:
        path.unlink(missing_ok=True)
        return
    counts, denominators, names = [], [], []
    for r in selected:
        b,t=r["metrics"]["balanced"],r["metrics"]["twins"]
        counts.append([d["correct"] for d in b["depths"]]+[t["visible"],t["masked"]])
        denominators.append([b["n"]]*3+[t["n"]]*2)
        names.append(r["model"]+" · "+r["phase"])
    rates=np.array(counts)/np.array(denominators)
    fig,ax=plt.subplots(figsize=(9.8,1.9+.43*len(selected)),layout="constrained")
    ax.imshow(rates,cmap="YlGnBu",vmin=0,vmax=1,aspect="auto")
    ax.set_xticks(range(5),["J1 verdict","J2 verdict","J3 verdict","Visible pair","Masked pair"])
    ax.set_yticks(range(len(names)),names)
    ax.xaxis.tick_top()
    ax.tick_params(length=0,pad=6)
    ax.axvline(2.5,color="white",linewidth=3)
    for i,row in enumerate(counts):
        for j,count in enumerate(row):
            ax.text(j,i,f"{count}/{denominators[i][j]}",ha="center",va="center",weight="bold",
                    color="white" if rates[i,j]>.57 else "#173b40")
    ax.set_title("Frozen judges on balanced traces and matched evidence pairs",loc="left",pad=16)
    ax.set_xlabel("Verdict scores count solver traces. Pair scores require two complete and correct Judge 3 reports.",fontsize=9,labelpad=9)
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.savefig(path,dpi=155,bbox_inches="tight")
    plt.close(fig)


def experiment_pages(study, dest):
    """Keep per-configuration evidence and the reason a run succeeded or failed accessible by run ID."""
    from .design import GITHUB
    for r in study["results"]:
        folder = dest/r["key"]
        raw = f"{GITHUB}/tree/main/results/new-judges/{r['key']}"
        method = (f"# {r['model']} · {r['phase']}\n\n{r['status']}. {r['result']}\n\n"
                  f"[Complete raw records]({raw}) · [Case and selection protocol](../../../newer-frozen-judges.md)")
        note = [f"# What this run showed\n\n{r['result']}"]
        if r.get("metrics"):
            method += "\n\n"+markdown(HEAD,list(depth_rows({"results":[r]})))
            for label,record in r["audit"]["examples"].items():
                note += [f"## A {'successful' if label=='passed' else 'failed'} evidence pair",
                         f"Problem `{record['expression']}`. The solver wrote `{record['trace']}`. Judge 1 wrote `{record['first']}`.",
                         markdown(["Judge 2 review","Judge 3 wrote","Checker expected"],
                                  list(zip(record["reviews"],record["outputs"],record["expected"],strict=True)))]
            method += f"\n\nThe release checked {r['audit']['calls']} scored calls against the original prompts, raw generated text and independent arithmetic values. The masked twins returned identical token sequences on {r['audit']['matched_masked_outputs']}/{r['metrics']['twins']['n']} pairs."
            gpu = r.get("gpu")
            if gpu:
                method += ("\n\nWindows sampled the dedicated allocation of the llama.cpp process at up to "
                           f"{gpu['peak_dedicated_mib']:,.0f} MiB. At its last sample, per-process engine running time was "
                           +", ".join(f"{e['engine']} {e['seconds']:.1f} s" for e in gpu["engines"])+
                           ". Engine counters include model loading. Sampling can end before the final kernel completes. "
                           "[Windows GPU accounting](https://devblogs.microsoft.com/directx/gpus-in-the-task-manager/).")
        else:
            note += ["The archived attempt is excluded from accuracy comparisons. Its recorded termination reason is available in the raw evidence."]
        atomic(folder/"experiment.md",method+"\n")
        atomic(folder/"learnings.md","\n\n".join(note)+f"\n\n[Raw evidence]({raw}).\n")
