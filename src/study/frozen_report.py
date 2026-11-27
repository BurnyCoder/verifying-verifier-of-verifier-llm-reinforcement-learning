"""Use the completed fixed-trace receipts for side-by-side depth and evidence results."""

from functools import lru_cache

from .frozen_audit import audit
from .frozen_device import measured_engine_times
from .frozen_models import LOCAL_REPLICATES, MODELS
from .storage import atomic, read_json, rows
from .tables import markdown


HEAD = ["Model and cohort","J1 verdict","J2 verdict","J3 verdict","J3 visible pairs","J3 masked pairs","J3 fixes / new errors"]


@lru_cache(maxsize=16)
def released_audit(folder, receipt_time):
    """A completed receipt identifies immutable calls. Avoid re-reading them on every dashboard refresh."""
    return audit(folder, read_json(folder/"result.json"))


@lru_cache(maxsize=8)
def visible_requests(path, modified):
    """Index visible J3 twin calls. The timestamp invalidates the dashboard cache on a changed journal."""
    return {r["id"]:r for r in rows(path) if r["id"].startswith("twins/") and "/visible/" in r["id"]}


def compare_conversions(primary, alternate):
    """Match interventions by problem and review side before comparing text or model responses."""
    left = visible_requests(primary, primary.stat().st_mtime_ns)
    right = visible_requests(alternate, alternate.stat().st_mtime_ns)
    if not left or left.keys() != right.keys():
        raise ValueError("The two releases contain different visible twin request identities")
    def matches(field):
        return sum(item[field] == right[key][field] for key, item in left.items())
    return dict(calls=len(left), same_messages=matches("messages"), same_prompts=matches("rendered_prompt"),
                same_input_counts=matches("input_tokens"), same_outputs=matches("text"))


def conversion_findings(root, results):
    """Compare preregistered deployment replicates after seeing their scores. They cannot select the winner."""
    complete = {r["key"]:r for r in results if r.get("metrics")}
    findings = []
    for replica in LOCAL_REPLICATES:
        key = replica.key.removesuffix("-ollama")
        if key not in complete or replica.key not in complete:
            continue
        pair = [complete[k]["metrics"]["twins"] for k in (key, replica.key)]
        same = compare_conversions(root/key/"calls.jsonl", root/replica.key/"calls.jsonl")
        if 2*pair[0]["n"] != same["calls"] or pair[0]["n"] != pair[1]["n"]:
            raise ValueError("The release comparison is missing evidence pairs")
        findings.append(f"{replica.title} passed {pair[0]['visible']}/{pair[0]['n']} whole pairs with the Unsloth release and "
                        f"{pair[1]['visible']}/{pair[1]['n']} with the Ollama release. Of {same['calls']} matched visible reviews, "
                        f"{same['same_messages']} had identical messages, {same['same_prompts']} had identical rendered prompts, "
                        f"{same['same_input_counts']} had equal input token counts and {same['same_outputs']} produced identical output text.")
    return findings


def collect_frozen(root):
    results, failed = [], []
    for key in ("runtime-format-pilot",*[model.key for model in (*LOCAL_REPLICATES,*MODELS)],"q38-27b-iq1s","confirm-control","confirm-winner"):
        for fit in read_json(root/key/"fit.json",[]):
            if not fit["fit"]:
                failed.append(dict(key=key,file=fit["file"],reason=fit["reason"].splitlines()[0]))
        receipt = read_json(root/key/"result.json",{})
        if receipt:
            if receipt.get("metrics"):
                receipt["audit"] = released_audit(root/key,receipt["time"])
                receipt["devices"] = read_json(root/key/"gpu-graphs.json",{}).get("loads",[])
                samples = list(rows(root/key/"gpu-telemetry.jsonl"))
                if samples:
                    receipt["gpu"] = dict(peak_dedicated_mib=max(r["dedicated_bytes"] for r in samples)/2**20,
                                          engines=measured_engine_times(samples),last_sample=samples[-1]["time"])
            results.append({**receipt,"key":key})
    return dict(results=results,decision=read_json(root/"decision.json",{}),conversions=conversion_findings(root,results),fit_failures=failed)


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
            yield [f"{result['model']} · {result['phase']} · {cohort}", *values, *pairs, f"{record['fixed']} / {record['harmed']}"]


def frozen_text(study):
    records = list(depth_rows(study))
    parts = ["## Newer frozen judges on fixed solver answers"]
    if records:
        parts += ["Every depth grades the same solver responses within a cohort. A visible-pair success requires both complete audit records and the exact numerical correction. Each balanced problem contributes one valid trace and one invalid trace. The last column counts Judge 2 errors that Judge 3 fixed, followed by correct Judge 2 verdicts that Judge 3 overturned.",markdown(HEAD,records)]
    else:
        parts.append("No completed fixed-trace score has been released.")
    for r in study["results"]:
        if r.get("metrics"):
            costs = r["cost"]
            parts.append(f"{r['model']} ({r['phase']}, {r['file']}) used {costs['input_tokens']:,} input and {costs['output_tokens']:,} output tokens in {costs['elapsed_seconds']:.1f} seconds of end-to-end calls.")
        else:
            parts.append(f"{r['model']} · {r['status']}. {r['result']}.")
    parts.extend(interpretation(study))
    return "\n\n".join(parts)


def interpretation(study):
    """Keep the matched confirmation distinct from the exploratory comparison of file conversions."""
    parts = [f"{f['file']} failed the GPU fit check before generating any answers. {f['reason']}." for f in study.get("fit_failures",[])]
    if study.get("conversions"):
        parts += ["The comparison of two conversions of the same model was exploratory. Both used the same llama.cpp CUDA executable. The experiment varies each complete model file, so a specific conversion difference cannot be identified as the cause.",*study["conversions"]]
    decision = study["decision"]
    if decision:
        if decision.get('original_completed_selection'):
            old = next(r for r in study['results'] if r['key']==decision['original_completed_selection'])
            parts.append(f"Among the completed original screens, {old['model']} ranked first. The amended ranking also considers the separately restarted 27B file when it completes.")
        selected = next((r for r in study["results"] if r["key"]==decision.get("selected")),None)
        if selected:
            parts.append(f"The screen selected {selected['model']} ({selected['file']}) for independent confirmation against the original frozen model.")
        parts.append(decision["result"]+".")
        for metric, estimate in decision.get("estimates",{}).items():
            lo,hi = estimate["ci"]
            parts.append(f"The candidate-minus-control difference in {metric.replace('_',' ')} was {estimate['delta']*100:+.2f} percentage points on {estimate['n']} paired problems (95% interval {100*lo:+.2f} to {100*hi:+.2f}).")
        if decision.get("estimates"):
            parts.append("Intervals resample confirmation problems in pairs and condition on the deployed model files. The solver responses were fixed throughout. Measuring what the solver learns from these rewards requires the deferred online comparison.")
    return parts


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
        for fit in study.get("fit_failures",[]):
            if fit["key"]==r["key"]:
                note.append(f"{fit['file']} failed the pre-inference GPU check. {fit['reason']}.")
        if r.get("metrics"):
            method += "\n\n"+markdown(HEAD,list(depth_rows({"results":[r]})))
            for label,record in r["audit"]["examples"].items():
                note += [f"## A {'successful' if label=='passed' else 'failed'} evidence pair",
                         f"Problem `{record['expression']}`. The solver wrote `{record['trace']}`. Judge 1 wrote `{record['first']}`.",
                         markdown(["Judge 2 review","Judge 3 wrote","Checker expected"],
                                  list(zip(record["reviews"],record["outputs"],record["expected"],strict=True)))]
            method += f"\n\nThe release checked {r['audit']['calls']} scored calls against the original prompts, raw generated text and independent arithmetic values. The masked twins returned identical token sequences on {r['audit']['matched_masked_outputs']}/{r['metrics']['twins']['n']} pairs."
            positions=r["audit"]["error_positions"]
            method += f" The balanced invalid traces contained {positions['nonfinal']} first errors before the final step and {positions['final']} at the final step."
            if r.get("devices"):
                total=sum(x["graph_assignments"]["CUDA0"] for x in r["devices"])
                method += f" The server recorded {total:,} compute graph assignments across the measured loads. Every assignment used CUDA0."
            gpu = r.get("gpu")
            if gpu:
                method += ("\n\nWindows sampled the dedicated allocation of the llama.cpp process at up to "
                           f"{gpu['peak_dedicated_mib']:,.0f} MiB. Measured active time between usable adjacent samples was "
                           +", ".join(f"{e['engine']} {e['seconds']:.1f} s across {e['interval_seconds']:.1f} s ({e['usable']} usable intervals, {e['discarded']} discarded)" for e in gpu["engines"])+
                           ". The sampling window can miss startup and final kernels. Discontinuities supply no time estimate. "
                           "[Windows timer counters](https://learn.microsoft.com/en-us/windows/win32/wmisdk/timer-algorithm-counter-types).")
        elif r.get('latency'):
            note += ["The throughput decision used recorded wall times before and after a reload of the same model. Each row is a completed call.",
                     markdown(['Call ID','Completion time (UTC)','Seconds'],[[c['id'],c['time'],f"{c['seconds']:.1f}"] for c in r['latency']['evidence']])]
        else:
            note += ["The archived attempt is excluded from accuracy comparisons. Its recorded termination reason is available in the raw evidence."]
        atomic(folder/"experiment.md",method+"\n")
        atomic(folder/"learnings.md","\n\n".join(note)+f"\n\n[Raw evidence]({raw}).\n")
