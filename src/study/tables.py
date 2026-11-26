"""Readable release tables derived from raw observations collected by the reporter."""

from .design import SEEDS


def rate(value):
    return "—" if value is None else f"{100 * value:.1f}%"


def points(value):
    return f"{100 * value:+.2f}"


def contrast_rows(data):
    """Keep confirmatory threshold decisions exclusive to the D3 versus D2 contrast."""
    for label, estimate in (("D3 − D2", data["primary"]), ("D3 − flat", data["flat"])):
        if "delta" not in estimate:
            continue
        yield [label, "Pooled", points(estimate["delta"]), *(points(x) for x in estimate["ci"])]
        for seed in map(str, SEEDS):
            yield [label, seed, points(estimate["per_seed"][seed]),
                   *(points(x) for x in estimate["seed_intervals"][seed])]


def replay_rows(run):
    """Show explicit denominators, including an empty class and every independent ballot."""
    for phase, results in (("Development", run["replay"]), ("Held out", run["test_replay"])):
        for r in results:
            if r["n"]:
                yield [phase, r["method"], rate(r["agreement"]),
                       "—" if r["evidence_correct"] is None else f"{r['evidence_correct']}/{r['n']}",
                       f"{r['false_accept']}/{r['invalid']}",
                       f"{r['false_reject']}/{r['valid']}", f"{r['malformed']}/{r['reports']}"]


def markdown(headers, records):
    lines = [headers, ["---"] * len(headers), *records]
    return "\n".join("| " + " | ".join(map(str, line)) + " |" for line in lines)


def training_method(run):
    if run["name"]=="base":
        return "The untrained Qwen solver and frozen reviewers provide the starting measurements."
    source = run["initial"] or "a fresh LoRA initialization"
    text = f"The {run['role']} adapter starts from {source} with seed {run['seed']}. Its reward rule is {run['reward']}. "
    if run["role"]!="solver":
        text += f"The judge corpus uses the {run['corpus']} solver. "
        return text + (f"The frozen teacher is {run['teacher']}." if run["teacher"] else "The checker labels the complete evidence record.")
    if run["reward"]=="oracle":
        return text + "The exact checker supplies the complete-trace reward."
    if run["reward"]=="flat":
        return text + "Three independent first-order calls vote on the same solver response."
    depth={"d1":1,"d2":2}.get(run["reward"],3)
    reviewers=", ".join(j or "the base model" for j in run["judges"][:depth])
    return text + f"Frozen reviewer calls in order use {reviewers}."


def run_evidence(run):
    """Record natural-review changes, transfer accuracy and measured computational cost."""
    sections = []
    replay = list(replay_rows(run))
    if replay:
        sections.extend(["### Replaying the same solver outputs",
                         markdown(["Split", "Rule", "Verdict agreement", "Exact evidence / traces", "False accepts / invalid", "False rejects / valid",
                                   "Malformed / reports"], replay),
                         "The flat panel contributes three ballots per trace. A zero denominator means the relevant class was absent."])
    shifts = []
    for split, n, fixed, harmed in (("Development", run["dev_n"], run["fixed"], run["harmed"]),
                                     ("Held out", run["test_review_n"], run["test_fixed"], run["test_harmed"])):
        if n:
            shifts.append([split, n, fixed, harmed, points((fixed - harmed) / n)])
    if shifts:
        sections.append(markdown(["Split", "Natural traces", "J3 fixes", "J3 harms", "D3 − D2 verdict accuracy (pp)"], shifts))
    twins = []
    for split, n, visible, masked in ((run["twin_split"], run["twins_n"], run["twins"], run["masked"]),
                                      ("Familiar layout, novel evidence", run["unseen_evidence"]["n"],
                                       run["unseen_evidence"]["visible"], run["unseen_evidence"]["masked"]),
                                      ("Unseen layout, familiar evidence", run["layout_evidence"]["n"],
                                       run["layout_evidence"]["visible"], run["layout_evidence"]["masked"]),
                                      ("Layout and evidence sign reversal", run["transfer_twin_n"],
                                       run["transfer_visible"], run["transfer_masked"])):
        if n:
            twins.append([split, n, rate(visible), rate(masked)])
    if twins:
        sections.extend(["### Paired evidence interventions",
                         markdown(["Split", "Problem pairs", "Whole pair exact", "Masked whole pair exact"], twins)])
        fields = []
        for condition, counts in run["evidence_fields"].items():
            if counts["reports"]:
                fields.append([condition, counts["reports"], counts["parsed"], counts["solution_bit"], counts["audit_bit"],
                               f"{counts['localized_and_repaired']}/{counts['faults']}"])
        if fields:
            sections.append(markdown(["Condition", "Twin reports", "Six fields parsed", "Correct solution bit",
                                      "Correct audit bit", "Fault located and repaired / faulty reviews"],fields))
        shared = sorted({name for name in run["evidence_sources"].values() if name != run["name"]})
        if shared:
            sections.append("These evidence measurements use the identical frozen reviewer from "+", ".join(shared)+". They are shared observations.")
    if run["role"] == "solver" and run["test_n"]:
        sections.extend(["### Held-out solver measures",
            markdown(["Complete trace", "Final integer", "Unseen layout", "Longer expression", "Correct named assignments among malformed"],
                     [[rate(run["test"]), rate(run["final_answer"]), rate(run["transfer"]["layout"]),
                       rate(run["transfer"]["long"]), run["test_named_correct"]]])])
        if run.get("family"):
            signed = run["test"] if run["family"]=="registered" else run["transfer"].get("original-difficulty")
            desc = " (same population as primary)" if run["family"]=="registered" else ""
            sections.append("Original signed-difficulty complete-trace accuracy"+desc+" was "+rate(signed)+".")
    if run["usage"]:
        usage = [[name, counts["calls"], counts["input_tokens"], counts["output_tokens"], f"{counts['gpu_seconds']:.2f}"]
                 for name, counts in run["usage"].items()]
        sections.extend(["### Training generation cost",
                         markdown(["Role", "Calls", "Input tokens", "Output tokens", "CUDA event seconds"], usage)])
    return "\n\n".join(sections)
