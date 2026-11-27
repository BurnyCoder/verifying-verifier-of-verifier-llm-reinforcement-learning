"""Use the completed fixed-trace receipts for side-by-side depth and evidence results."""

from .frozen_models import LOCAL_REPLICATES, MODELS
from .storage import read_json
from .tables import markdown


HEAD = ["Model and cohort","J1 verdict","J2 verdict","J3 verdict","J3 visible pairs","J3 masked pairs"]


def collect_frozen(root):
    results = []
    for key in ("runtime-format-pilot",*[model.key for model in (*LOCAL_REPLICATES,*MODELS)],"confirm-control","confirm-winner"):
        receipt = read_json(root/key/"result.json",{})
        if receipt:
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
