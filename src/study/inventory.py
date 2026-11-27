"""One release ledger for archived experiments, current work, and unobserved treatments."""

from .curriculum import FAMILIES, STYLES
from .design import GITHUB, PILOTS, ROUTES, matched_runs, matrix
from .frozen_models import LOCAL_REPLICATES, MODELS
from .matched_tables import cell
from .storage import read_json, rows
from .tables import markdown


HEADERS = ["Run", "Treatment or measurement", "Status", "Development or pilot result", "Held-out result"]
GUIDE = ("The original solver and judge adapters all use Qwen2.5-1.5B-Instruct. A solver score counts complete "
         "arithmetic traces. A trained judge score counts complete evidence records. Stack replays report verdict "
         "agreement at each depth on the same saved answers. Pending means the phase has no completed measurement. "
         "A dash marks an inapplicable endpoint. Timing and calibration are outside the primary comparison.")


def training_observations(root):
    """Portable public progress records retain timestamps without copying an unfinished training journal."""
    snapshot = {}
    for recipe_path in (root / "calibrated").glob("*/recipe.json"):
        folder = recipe_path.parent
        if (folder / "trained.json").is_file():
            continue
        observation = next(reversed(list(rows(folder / "cost.jsonl"))), {})
        recipe = read_json(recipe_path)
        snapshot[folder.name] = {"target": recipe["updates"], "step": observation.get("step", 0),
                                 "started": recipe.get("started")}
    return snapshot


def treatment(spec):
    """Identify both the active role and the origin of its reward for this optimizer block."""
    role = spec.role.upper()
    if spec.role != "solver":
        teacher = spec.teacher or "exact full report"
        return f"{role} learns from {teacher}" + (f", continuing {spec.initial}" if spec.initial else "")
    rules = {"flat":"three independent votes", "oracle":"exact trace", "hybrid":"J3 and checker",
             "shuffle":"within-group shuffled J3"}
    reward = rules.get(spec.reward, spec.reward.upper())
    depth = {"d1":1, "d2":2, "d3":3}.get(spec.reward, 0)
    fitted = [j for j in spec.judges[:depth] if j]
    if fitted:
        route = "top-down" if any("top" in j for j in fitted) else "exact-trained"
        reward += f", {len(fitted)} {route} judge{'s' if len(fitted)>1 else ''}"
    return ("Continue solver" if spec.initial else "Fresh solver") + f", {reward}, seed {spec.seed}"


def inventory(root, profile, observed, contrasts=None):
    """Join planned treatments to phase-completion receipts. A real zero is a measured score."""
    ledger = []

    def add(group, key, description, status="Planned", result="Pending", held="—", evidence=None):
        target = "blob" if evidence and (root/evidence).is_file() else "tree"
        ledger.append(dict(group=group, id=key, treatment=description, status=status, result=result,
                           held_out=held, evidence=f"{GITHUB}/{target}/main/results/{evidence}" if evidence else None))

    def measured(group, key, description, path, score, *, held="—"):
        receipt = read_json(root / path)
        add(group, key, description, "Complete" if receipt else "Planned",
            score(receipt) if receipt else "Pending", held, path if receipt else None)

    historical = "Original signed arithmetic"
    if profile:
        for name in ("base", "d3-17"):
            batch = list(rows(root/name/"replay.jsonl")) if (root/name/"development.json").is_file() else []
            add(historical, "original/"+name, "Untrained solver" if name=="base" else "Fresh solver, frozen J3, seed 17",
                "Archived" if batch else "Planned", cell(sum(r["correct"] for r in batch), len(batch)) if batch else "Pending",
                "Deferred", name if batch else None)
    measured(historical, "original/timing", "Disposable solver, frozen J3, wall-clock pilot", "timing/trained.json",
             lambda m:f"{m['updates']} updates in {m['elapsed_seconds']:.1f} s")
    if profile:
        add(historical, "original/registered-only", "Other original signed treatments and sealed evaluation",
            "Superseded in this campaign", "See calibrated arms below", "Deferred")

    group = "Difficulty and learning controls"
    calibration = root / "learnability"
    screen = read_json(calibration/"screen.json", {})
    cells = {(c["family"],c["style"]):c for c in screen.get("cells", [])}
    for family in FAMILIES:
        for style in STYLES:
            c = cells.get((family,style))
            result = cell(round(c["greedy_exact"]*c["problems"]),c["problems"]) if c else "Pending"
            add(group, f"screen/{family}-{style}", "Frozen solver, greedy trace", "Complete" if c else "Planned", result,
                evidence="learnability/screen.json" if c else None)
    measured(group, "learnability/confirm", "Fresh difficulty confirmation, greedy trace", "learnability/confirm.json",
             lambda m:cell(round(m["cell"]["greedy_exact"]*m["cell"]["problems"]),m["cell"]["problems"]))
    measured(group, "learnability/audit", "Frozen balanced verdicts at J1/J2/J3 and visible J3 twins", "learnability/audit.json",
             lambda m:" / ".join(f"{r['balanced_accuracy']:.1%}" for r in m["judges"])+f", twins {round(m['visible']*m['pairs'])}/{m['pairs']}")
    for name in ("base", *PILOTS):
        objective = {"base":"Frozen solver","learn-oracle-17":"Solver, exact reward","learn-shuffle-17":"Solver, shuffled exact reward"}[name]
        measured(group, "validation/"+name, objective+", independent validation", f"learnability/evaluations/{name}.json",
                 lambda m:cell(m["correct"],m["n"]))

    cohort = "calibrated" if profile else "original"
    source = root / cohort if profile else root
    records = {r["name"]:r for r in observed}
    snapshot = read_json(root/"run-snapshot.json",{})
    deferred = snapshot.get("campaign")=="deferred"
    archived_state = snapshot.get("training",{})
    progress = {**archived_state, **training_observations(root)}
    extras = matched_runs(profile)
    for spec in (None, *matrix(profile), *extras):
        name = spec.name if spec else "base"
        r = records.get(name,{})
        group = "Matched trained judge depths" if spec in extras else "Main solver and judge study"
        state = "Deferred" if deferred else "Planned"
        if r.get("completed_final"):
            state = "Final complete"
        elif r.get("completed_development"):
            state = "Development complete"
        elif (source/name/"trained.json").is_file():
            state = "Trained, development pending"
        elif name in progress:
            p = progress[name]
            state = f"Training started · {p['step']}/{p['target']}"
            stopped = archived_state.get(name,{})
            if stopped.get("status")=="Paused" and p["step"] <= stopped["step"]:
                state = f"Paused · {stopped['step']}/{stopped['target']} logged, checkpoint {stopped['resume_step']}"
        def result(split, complete):
            n = r.get(split+"_n",0)
            return cell(round(r[split]*n),n) if complete and n and r.get(split) is not None else "Pending"
        held = result("test",r.get("completed_final"))
        add(group, f"{cohort}/{name}", treatment(spec) if spec else "Frozen starting solver", state,
            result("dev",r.get("completed_development")), "Deferred" if deferred and held=="Pending" else held,
            (f"calibrated/{name}" if profile else name) if (source/name).is_dir() else None)
    for route in ROUTES:
        base = f"matched-depth/{route}-"
        def agreement(phase):
            if not (source/(base+phase+".json")).is_file():
                return "Pending"
            records = list(rows(source/(base+phase+".jsonl")))
            return " · ".join(f"{sum(r['verdicts'][i]==r['correct'] for r in records)}/{len(records)}" for i in range(3))
        dev, final = agreement("development"), agreement("final")
        status = "Final complete" if final!="Pending" else "Development complete" if dev!="Pending" else "Planned"
        add("Matched trained judge depths", "replay/"+route, "Frozen fitted stack, J1/J2/J3 on identical base traces",
            status, dev, "Deferred" if deferred and final=="Pending" else final, "calibrated/matched-depth" if dev!="Pending" else None)

    for arm, description in (("primary", "D3 minus D2, paired across seeds 17, 29 and 43"),
                             ("flat", "D3 minus three independent votes, same seeds")):
        effect = (contrasts or {}).get(arm, {})
        final = "Pending"
        if "delta" in effect:
            low, high = effect["ci"]
            final = f"{100*effect['delta']:+.2f} pp [{100*low:+.2f}, {100*high:+.2f}]"
        add("Final evaluation and transfer", "analysis/"+arm, description, "Complete" if final!="Pending" else "Deferred" if deferred else "Planned",
            "—", final)
    if profile:
        solvers = ["base", *(s.name for s in (*matrix(profile), *extras) if s.role=="solver")]
        for split, label in (("test","Primary arithmetic, 2,048 questions"),("layout","Reserved tree layouts, 128 questions"),
                             ("long","Longer expressions, 128 questions"),("original-difficulty","Signed arithmetic, 2,048 questions")):
            if split=="original-difficulty" and profile["family"]=="registered":
                continue
            done = [name for name in solvers if records.get(name,{}).get("completed_final")]
            add("Final evaluation and transfer", "cohort/"+split, label+" per solver",
                "Complete" if len(done)==len(solvers) else "In progress" if done else "Deferred" if deferred else "Planned", "—",
                f"{len(done)}/{len(solvers)} checkpoints evaluated" if done else "Pending")
        for field, label in (("mechanism","Familiar evidence and layout"),("unseen-evidence","Unseen error pattern"),
                             ("layout-evidence","Reserved layout"),("transfer-evidence","Unseen error and reserved layout")):
            eligible = ["base",*(s.name for s in matrix(profile) if s.role=="j3" or s.name in
                                ("exact-prefix3","top-prefix3","alt-exact-solver","alt-top-solver"))]
            done = sum(bool(records.get(n,{}).get("completed_final")) for n in eligible)
            add("Final evaluation and transfer","cohort/"+field,label+", 128 evidence pairs, visible and masked",
                "Complete" if done==len(eligible) else "In progress" if done else "Deferred" if deferred else "Planned", "—",
                f"{done}/{len(eligible)} eligible checkpoints evaluated" if done else "Pending")
    for key, description, conditional in (
        ("runtime-format-pilot","Qwen3.5-9B server-output formatting diagnostic",False),
        *((m.key,m.title+" frozen, Ollama Q4_K_M deployment replicate",False) for m in LOCAL_REPLICATES),
        *((m.key, m.title+" frozen, same-runtime screen", False) for m in MODELS),
        ("q38-27b-iq1s", "Frozen 27B IQ1_S, fresh screen conditional on sustained latency at higher precision", True),
        ("confirm-control", "Frozen Qwen2.5 control, fresh confirmation", True),
        ("confirm-winner", "Selected newer frozen judge, fresh confirmation", True),
        ("winner-d2", "Fresh Qwen2.5 solver, selected frozen J2 reward, seed 17", True),
        ("winner-d3", "Fresh Qwen2.5 solver, selected frozen J3 reward, seed 17", True),
    ):
        folder = root/"new-judges"/key
        receipt = read_json(folder/"result.json",{})
        active = read_json(folder/"progress.json",{})
        planned = "Conditional, later day" if deferred and key.startswith("winner-d") else "Conditional" if conditional else "Planned"
        if active:
            planned = active["status"] + (f" · {active['calls']}/{active['target']} calls" if "calls" in active else "")
        state = receipt.get("status", planned)
        decision = read_json(root/"new-judges/decision.json",{})
        if key.startswith("winner-d") and decision:
            state = "Eligible, deferred" if decision.get("online_gate") else "Gate not met" if "online_gate" in decision else "Deferred"
            plan = read_json(root/"new-judges/online-plan.json")
            if plan and decision.get("online_gate"):
                from .online_report import arm_progress
                arm = arm_progress(folder, plan["updates"])
                state = arm["status"]
                description += " · "+plan["judge"]
                if arm["n"]:
                    receipt["result"] = cell(arm["correct"],arm["n"])+" exact solver traces"
        if key=="confirm-winner" and receipt.get("model"):
            description += " · "+receipt["model"]
        add("Newer frozen Qwen judges", "new-judges/"+key, description, state, receipt.get("result","Pending"),
            evidence="new-judges/"+key if folder.is_dir() else None)
    return ledger


def grouped(ledger):
    """Group by study phase while preserving the original ordering within each phase."""
    for name in dict.fromkeys(r["group"] for r in ledger):
        yield name, [r for r in ledger if r["group"]==name]


def inventory_markdown(ledger):
    parts = [GUIDE]
    for group, records in grouped(ledger):
        def fields(r):
            key = f"[{r['id']}]({r['evidence']})" if r["evidence"] else r["id"]
            return [key,r["treatment"],r["status"],r["result"],r["held_out"]]
        parts.extend(["### "+group, markdown(HEADERS, [fields(r) for r in records])])
    return "\n\n".join(parts)
