"""Rebuild all public numbers from complete observations and attach denominators."""

from collections import defaultdict
from datetime import datetime
from math import sqrt
from statistics import NormalDist, mean
from zoneinfo import ZoneInfo

from .analysis import evidence_fields, paired_comparison, paired_primary, replay_metrics
from .depth_review import collect_depth_review, readme_depth, review_text as depth_review_text
from .paired_examples import differing_examples, paired_text
from .trajectory import late_rewards, save_trajectory_figure
from .design import GITHUB, MATCHED_NAMES, PAGES, PILOTS, Run, matched_runs, matrix
from .final_review import review_completed, review_text as final_review_text
from .learnability_report import collect_learnability, learnability_text, learning_figure
from .learning_review import check_release, review_text
from .inventory import GUIDE, HEADERS, grouped, inventory, inventory_markdown
from .frozen_report import collect_frozen, confirmation_headline, confirmation_review_text, depth_rows as frozen_rows, experiment_pages, frozen_text, interpretation, plot_scores
from .matched_tables import accuracy_grid, grid_markdown
from . import online_report
from .records import named_values
from .storage import ORIGINAL_RESULTS, ROOT, atomic, read_json, rows, write_json
from .tables import contrast_rows, markdown, rate as percent, run_evidence, training_method

DOCS = ROOT / "docs"
REPORTS = ROOT / "reports"


def fraction(records, key):
    return mean(r[key] for r in records) if records else None


def wilson(proportion, n):
    """Wilson score endpoints for a descriptive binomial proportion on distinct problems."""
    z=NormalDist().inv_cdf(.975)
    denominator=1+z*z/n
    center=(proportion+z*z/(2*n))/denominator
    radius=z*sqrt(proportion*(1-proportion)/n+z*z/(4*n*n))/denominator
    return max(0.0,center-radius),min(1.0,center+radius)


def collect():
    """Keep live training/dev observations available. Only completed final evaluations enter tables."""
    calibrated = ORIGINAL_RESULTS / "calibrated"
    profile = read_json(calibrated/"profile.json", {})
    source = calibrated if profile else ORIGINAL_RESULTS
    manifest = {r.name: r for r in matrix(profile)}
    registered=len(manifest)
    manifest.update((r.name,r) for r in matched_runs(profile))
    learning=collect_learnability(ORIGINAL_RESULTS)
    chosen=(learning["screen"] or {}).get("selected")
    if chosen:
        for name in PILOTS:
            manifest[name]=Run(name,reward="oracle" if name==PILOTS[0] else "oracle-shuffle",
                               family=chosen["family"],prompt_style=chosen["style"])
    runs, outcomes = [], {}
    for name in ("base", *manifest):
        target = (ORIGINAL_RESULTS if name in PILOTS else source) / name
        if not target.is_dir():
            continue
        spec = manifest.get(name)
        role = spec.role if spec else "solver"
        training = list(rows(target/"rollouts.jsonl"))
        dev = list(rows(target/"replay.jsonl"))
        final = read_json(target/"final.json")
        test = list(rows(target/"test.jsonl")) if final else []
        test_reviews = list(rows(target/"judge-test.jsonl")) if final else []
        transfer_twins = list(rows(target/"transfer-evidence.jsonl")) if final else []
        unseen_twins = list(rows(target/"unseen-evidence.jsonl")) if final else []
        layout_twins = list(rows(target/"layout-evidence.jsonl")) if final else []
        if test:
            outcomes[name] = {r["key"]: r["correct"] for r in test}
        twins = list(rows(target/("mechanism.jsonl" if final and (target/"mechanism.jsonl").exists()
                                  else "development-twins.jsonl")))
        groups = defaultdict(list)
        for r in training:
            groups[r["step"]].append(r)
        curves = [dict(step=k+1, reward=mean(r["reward"] for r in group), exact=mean(r["label"] for r in group))
                  for k, group in sorted(groups.items()) if len(group) == 4]
        role_acc = (mean(r["full_report_correct"][int(role[1:])-1] for r in dev)
                    if dev and role != "solver" else fraction(dev, "correct"))
        reports = list(rows(target/"metrics.jsonl"))
        trained = read_json(target/"trained.json", {})
        examples = []
        for match in (0, 1):
            examples.extend(r for r in [next((r for r in dev if r["correct"] == match), None)] if r)
        heldout = test if role == "solver" else test_reviews
        heldout_exact = (fraction(test, "correct") if role == "solver" else
                         mean(r["full_report_correct"][int(role[1:])-1] for r in heldout) if heldout else None)
        common_example = None
        if dev:
            from .domain import Problem
            from .records import expected, render
            e = dev[0]
            depth = 0 if role == "solver" else int(role[1:])
            actual = e["trace"] if depth == 0 else e["reports"][depth-1]
            reference = (e["expected_values"] if depth == 0 else
                         expected(Problem.from_expression(e["expression"]), e["trace"], e["reports"][:depth-1]))
            matched = e["correct"] if depth == 0 else e["full_report_correct"][depth-1]
            common_example = dict(key=e["key"], expression=e["expression"], actual=actual,
                                  expected=render(reference), correct=matched)
        runs.append(dict(name=name, role=role, reward=spec.reward if spec else "untrained", supplemental=name in MATCHED_NAMES,
                         diagnostic=name in PILOTS, family=spec.family if spec else profile.get("family"),
                         seed=spec.seed if spec else 17, updates=trained.get("updates"), observations=len(training),
                         initial=spec.initial if spec else None, judges=spec.judges if spec else (None,)*3,
                         teacher=spec.teacher if spec else None, corpus=spec.corpus if spec else None,
                         train_exact=fraction(training,"label"), train_reward=fraction(training,"reward"),
                         positive_on_incorrect=sum(r["reward"]==1 and r["label"]==0 for r in training),
                         zero_on_correct=sum(r["reward"]==0 and r["label"]==1 for r in training),
                         zero_groups=sum(len({r["reward"] for r in group}) == 1 for group in groups.values() if len(group)==4),
                         groups=len(curves), dev_n=len(dev), dev=role_acc, dev_final=fraction(dev,"final_correct"),
                         dev_correct_n=sum(r["correct"] for r in dev),
                         dev_malformed=sum(r["malformed"] for r in dev),
                         dev_named_correct=sum(r["malformed"] and named_values(r["trace"],len(r["expected_values"]))==tuple(r["expected_values"]) for r in dev),
                         test_named_correct=sum(r["malformed"] and named_values(r["trace"],len(r["expected_values"]))==tuple(r["expected_values"]) for r in test),
                         test_n=len(heldout), test=heldout_exact, final_answer=fraction(test,"final_correct"),
                         fixed=sum(r["fixed"] for r in dev), harmed=sum(r["harmed"] for r in dev),
                         test_review_n=len(test_reviews), test_fixed=sum(r["fixed"] for r in test_reviews),
                         test_harmed=sum(r["harmed"] for r in test_reviews), test_replay=replay_metrics(test_reviews),
                         twins_n=len(twins), twins=fraction(twins,"visible_pair"), masked=fraction(twins,"masked_pair"),
                         evidence_fields={mode:evidence_fields(twins,mode) for mode in ("visible","masked")},
                         transfer_twin_n=len(transfer_twins), transfer_visible=fraction(transfer_twins,"visible_pair"),
                         transfer_masked=fraction(transfer_twins,"masked_pair"),
                         unseen_evidence=dict(n=len(unseen_twins),visible=fraction(unseen_twins,"visible_pair"),masked=fraction(unseen_twins,"masked_pair")),
                         layout_evidence=dict(n=len(layout_twins),visible=fraction(layout_twins,"visible_pair"),masked=fraction(layout_twins,"masked_pair")),
                         evidence_sources=(final or read_json(target/"development.json",{})).get("evidence_sources",{}),
                         twin_split=twins[0]["split"] if twins else None, paired_example=twins[0] if twins else None,
                         replay=replay_metrics(dev), curves=curves, logs=reports, examples=examples, common_example=common_example,
                         usage=trained.get("usage", {}), elapsed_seconds=trained.get("elapsed_seconds"),
                         transfer={s: fraction(list(rows(target/(s+".jsonl"))), "correct")
                                   for s in ("layout","long","original-difficulty")} if final else {},
                         completed_final=bool(final), completed_development=(target/"development.json").is_file()))
    archive = []
    if profile:
        for name in ("base", "d3-17"):
            target = ORIGINAL_RESULTS / name
            if (target/"development.json").exists():
                sample = list(rows(target/"replay.jsonl"))
                archive.append(dict(name=name, correct=sum(r["correct"] for r in sample), n=len(sample)))
    contrasts = dict(primary=paired_primary(outcomes), flat=paired_comparison(outcomes,"flat"))
    return dict(runs=runs, inventory=inventory(ORIGINAL_RESULTS,profile,runs,contrasts),
                online_solvers=online_report.collect_online(ORIGINAL_RESULTS/"new-judges"),
                newer_judges=collect_frozen(ORIGINAL_RESULTS/"new-judges"), matched_depth=accuracy_grid(source,profile),
                **contrasts, planned=registered,
                learnability=learning, profile=profile, original_development=archive,
                budget=read_json(source/"budget.json"), sealed=(source/"seal.json").is_file(),
                completed=(source/"completed.json").is_file())


def scores_table(data):
    head = "| Run | Updated role | Updates | Development exact | Development n | Held-out exact | Held-out n |\n|---|---|---:|---:|---:|---:|---:|"
    values = [f"| {r['name']} | {r['role']} | {r['updates'] if r['updates'] is not None else '—'} | {percent(r['dev'])} | {r['dev_n']} | {percent(r['test'])} | {r['test_n']} |" for r in data["runs"]]
    return "\n".join([head, *values]) if values else "Model observations are pending."


def figures(data):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch

    dest = DOCS/"assets"
    dest.mkdir(parents=True, exist_ok=True)
    plot_scores(data["newer_judges"],dest/"frozen-judge-scores.png")
    learning_figure(data["learnability"],dest/"learnability.png")
    colors = ("#1e5260", "#177267", "#b65127")
    fig, ax = plt.subplots(figsize=(11, 2.45))
    ax.set(xlim=(0, 11), ylim=(0, 2.5))
    ax.axis("off")
    for i, (title, sub) in enumerate((("Solver","step values"),("Judge 1","solution evidence"),
                                      ("Judge 2","review of Judge 1"),("Judge 3","review of Judge 2"))):
        x = .15+2.75*i
        ax.add_patch(FancyBboxPatch((x, .88), 2.15, .95, boxstyle="round,pad=.07",
                                    fc="#e8f3f1", ec=colors[0], linewidth=1.5))
        ax.text(x+1.075, 1.49, title, ha="center", fontsize=13, weight="bold", color=colors[0])
        ax.text(x+1.075, 1.1, sub, ha="center", fontsize=10)
        if i < 3:
            ax.annotate("", (x+2.65, 1.35), (x+2.23,1.35), arrowprops={"arrowstyle":"->","color":colors[0]})
    ax.text(.12,2.2,"Each reviewer receives the original problem, solver trace and all preceding reports.",
            fontsize=10,color=colors[0])
    ax.plot([9.475,9.475,1.225],[.81,.50,.50],color=colors[1],linewidth=1.3)
    ax.annotate("",(1.225,.82),(1.225,.48),arrowprops={"arrowstyle":"->","color":colors[1]})
    ax.text(5.35,.51,"Final solution bit supplies the solver’s GRPO reward",ha="center",va="center",
            fontsize=9.5,color=colors[1],bbox={"facecolor":"white","edgecolor":"none","pad":2})
    ax.text(.12,.09,"The independent checker labels every field and supplies the exact and hybrid reward arms.",
            fontsize=9.5, color=colors[0])
    fig.tight_layout()
    fig.savefig(dest/"architecture.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    scored = [r for r in data["runs"] if r["dev"] is not None and r["role"] == "solver"]
    if scored:
        fig, ax = plt.subplots(figsize=(8, max(2.8,.33*len(scored)+1)))
        rates=[r["dev"] for r in scored]
        intervals=[wilson(r["dev"],r["dev_n"]) for r in scored]
        errors=[[max(0.0,p-lo) for p,(lo,hi) in zip(rates,intervals,strict=True)],
                [max(0.0,hi-p) for p,(lo,hi) in zip(rates,intervals,strict=True)]]
        ax.barh([r["name"] for r in scored], rates, color=colors[1],xerr=errors,capsize=3)
        ax.set(xlim=(0,1), xlabel="Complete-trace development accuracy with 95% Wilson intervals")
        ax.invert_yaxis()
        fig.tight_layout()
        fig.savefig(dest/"outcomes.png", dpi=140)
        plt.close(fig)
    if "delta" in data["primary"]:
        # Plot the signed effect for fixed seeds and the pooled contrasts on a shared linear scale.
        fig, ax = plt.subplots(figsize=(8, 4), constrained_layout=True)
        i = 0
        for label, estimate in (("D3 − D2", data["primary"]), ("D3 − flat", data["flat"])):
            if "delta" not in estimate:
                continue
            for seed, value in [("Pooled", estimate["delta"]), *estimate["per_seed"].items()]:
                lo, hi = estimate["ci"] if seed=="Pooled" else estimate["seed_intervals"][seed]
                ax.hlines(i, 100*lo, 100*hi, color=colors[0])
                ax.plot(100*value, i, "D" if seed=="Pooled" else "o", color=colors[0])
                ax.text(-.015,i,f"{label} · {seed}",transform=ax.get_yaxis_transform(),ha="right",va="center")
                i += 1
        ax.axvline(0,color="#536867",linewidth=1)
        ax.axvline(3,color=colors[2],linestyle="--",label="D3 − D2 practical target")
        ax.set(yticks=[],xlabel="Difference in held-out complete-trace accuracy (percentage points)")
        ax.invert_yaxis()
        ax.legend(loc="best")
        fig.savefig(dest/"paired-outcomes.png",dpi=145,bbox_inches="tight")
        plt.close(fig)
    examples = [r for r in data["runs"] if r["common_example"]]
    if examples:
        # All rows show the same preselected development problem, regardless of the resulting grades.
        fig, ax = plt.subplots(figsize=(11, max(2.4,.4*len(examples)+1.4)))
        ax.axis("off")
        ax.set_title("First development problem  ·  "+examples[0]["common_example"]["expression"],loc="left",pad=12)
        displayed=[]
        for r in examples:
            e=r["common_example"]
            output=" ".join(e["actual"].split())
            shown=output if len(output)<=37 else output[:36]+"…"
            displayed.append([r["name"],r["role"],shown,e["expected"],"Correct" if e["correct"] else "Incorrect"])
        table=ax.table(cellText=displayed,colLabels=["Run","Role","Model output","Exact record","Grade"],
                       colWidths=[.20,.10,.34,.23,.13],cellLoc="left",colLoc="left",bbox=[0,0,1,.98])
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        for (row,column),cell in table.get_celld().items():
            cell.set_edgecolor("#d3dfdc")
            if row==0:
                cell.set_facecolor("#dceeea")
            elif column==4:
                cell.set_facecolor("#ddf2e7" if examples[row-1]["common_example"]["correct"] else "#f9e3d8")
        fig.tight_layout()
        fig.savefig(dest/"examples.png",dpi=145,bbox_inches="tight")
        plt.close(fig)
    monitored = next((r for r in data["runs"] if r["name"]=="d3-17" and r["curves"]), None)
    if monitored:
        fig, axes = plt.subplots(2, 1, figsize=(8,5.3), constrained_layout=True)
        for key, label, c in (("reward","Judge reward",colors[0]),("exact","Exact correctness",colors[2])):
            curves = monitored["curves"]
            axes[0].plot([x["step"] for x in curves], [x[key] for x in curves], alpha=.85, label=label, color=c)
        axes[0].set(ylabel="Fraction per group", ylim=(-.03,1.03))
        axes[0].legend()
        loss = [r for r in monitored["logs"] if r.get("loss") is not None]
        axes[1].plot([r["step"] for r in loss],[r["loss"] for r in loss],color=colors[1])
        axes[1].set(xlabel="Optimizer update",ylabel="GRPO loss")
        fig.savefig(dest/"training.png",dpi=140)
        plt.close(fig)
    trajectory = data.get("depth_review", [])
    if trajectory:
        save_trajectory_figure(trajectory[0], dest/"depth-trajectory.png")
    # A fresh replication can share the report directory with a previously published data set.
    # Remove only generated figures that the current evidence did not produce.
    for filename, available in (("outcomes.png",scored), ("examples.png",examples), ("training.png",monitored),
                                ("paired-outcomes.png","delta" in data["primary"]), ("depth-trajectory.png",trajectory)):
        if not available:
            (dest/filename).unlink(missing_ok=True)


def paper(data, date):
    from pathlib import Path
    from xml.sax.saxutils import escape
    from matplotlib import get_data_path
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    styles = getSampleStyleSheet()
    # Embed the same Unicode fonts used by the plots so minus signs and author punctuation travel with the PDF.
    fonts = Path(get_data_path())/"fonts/ttf"
    variants = {"Helvetica":"", "Helvetica-Bold":"-Bold", "Helvetica-Oblique":"-Oblique",
                "Helvetica-BoldOblique":"-BoldOblique"}
    for suffix in variants.values():
        name="StudySans"+suffix
        if name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(name,str(fonts/("DejaVuSans"+suffix+".ttf"))))
    pdfmetrics.registerFontFamily("StudySans", normal="StudySans", bold="StudySans-Bold",
                                  italic="StudySans-Oblique", boldItalic="StudySans-BoldOblique")
    for style in styles.byName.values():
        previous_font=getattr(style,"fontName",None)
        if previous_font in variants:
            style.fontName="StudySans"+variants[previous_font]
    story = []
    def line(text, style="BodyText"):
        paragraph = Paragraph(text, styles[style])
        if style.startswith("Heading"):
            paragraph.keepWithNext = True
        story.append(paragraph)
    def table(headers, body):
        t = Table([headers,*body], repeatRows=1, hAlign="LEFT")
        t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#dceeea")),
                               ("FONTNAME",(0,0),(-1,-1),"StudySans"),
                               ("FONTSIZE",(0,0),(-1,-1),8.5),("VALIGN",(0,0),(-1,-1),"TOP"),
                               ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#f5f7f6")])]))
        before=Spacer(1,2*mm)
        before.keepWithNext=True
        story.extend([before,t,Spacer(1,2*mm)])
    line("Does a third LLM judge improve GRPO rewards?", "Title")
    line("Libor “Burny” Burian · "+date, "Heading3")
    line("Abstract","Heading2")
    line("A solver submits an integer calculation trace. Three successive language-model calls grade the trace, audit the first judgment and audit the second judgment. An independent integer checker can evaluate every field. We test the incremental effect of the third review on online GRPO and its ability to detect an evidence-only error in another judge's report. The registered primary comparison currently has status <b>"+data["primary"]["status"]+"</b>.")
    frozen_lead=confirmation_headline(data['newer_judges'])
    if frozen_lead:
        line(escape(frozen_lead))
    if data["online_solvers"].get("comparison"):
        line(escape(online_report.conclusion(data["online_solvers"])))
    line("Motivation and related work","Heading2")
    line("Wen et al. studied third-order pairwise critique and reward-model-guided best-of-N selection [1]. DeepSeekMath-V2 used a learned meta-verifier to review identified proof defects [2]. Our intervention uses the terminal solution verdict as an online policy reward and tests the review itself through an exact counterfactual. Comparing a chain with three independent votes measures the contribution of reviewing previous claims at a comparable generation budget.")
    story.append(Image(str(DOCS/"assets/architecture.png"), width=164*mm, height=37*mm))
    line("Methods","Heading2")
    line("The Reasoning Gym-derived sampler produces signed-integer expression trees [3]. Each operation has a numbered result. A report names the first erroneous step and its correction, following the first-error formulation used by ProcessBench [4]. An audit identifies the first erroneous field in the previous report, its replacement, and the final verdict on the original solution. A correct final value with a wrong intermediate step fails the complete-trace metric.")
    line("Policies share the pinned Qwen2.5-1.5B-Instruct backbone and use separate NF4/LoRA role configurations. GRPO uses four samples per prompt, group-scaled rewards, a clipped ratio, and a zero KL coefficient [5]. Solver-only, judge-only and alternating stages isolate which component learns. The control arms use depth one, depth two, a three-vote panel, exact outcomes, exact-gated learned rewards, and within-group shuffled rewards.")
    story.append(PageBreak())
    line("Experimental design","Heading1")
    line("Executable evidence","Heading2")
    line("Judge 1 emits the solution bit, first faulty step and replacement integer. A correct trace uses step zero and repeats the root value. Missing or malformed input uses (0, -1, 0). Judges 2 and 3 first emit the preceding report's soundness, the one-based index of its first false field and the correct replacement. They then emit the corrected three-field solution record. Endorsing a sound rejection therefore earns the solver zero.")
    line("In the evidence-pair intervention, both Judge 2 reports have the same verdicts on Judge 1 and the solver. Their numerical supporting values differ. Judge 3 must endorse the sound report and reject the altered report with its exact field and replacement, while retaining the correct solution verdict in both. Masking the evidence makes the twin inputs identical. Whole-pair credit therefore also tests whether the visible evidence affects the decision.")
    line("Online training and supervision","Heading2")
    line("The policy samples four completions at temperature 0.8, with a ceiling of 48 new tokens each. For reward r in group g, TRL assigns advantage (r − mean(g)) / (sd(g) + 0.0001). A group with identical rewards supplies zero centered reward signal. The policy uses a clip width of 0.2 and constant learning rate 0.00003. The quantized backbone stays frozen. The active role updates rank-16 LoRA adapters with alpha 32 on the query, key, value and output projections. This configuration fits the local accelerator and fixes trainable capacity across reward comparisons. [5, 7–9]")
    line("The exact judge route awards one only for an entire matching report. In the top-down route, a frozen higher judge's soundness bit rewards the lower judge. Both routes use the same examples and update budgets for each matched role. One in four judge-corpus entries uses a natural train-split trace and preceding reports. The remaining entries use constructed traces and controlled predecessor errors. Alternating blocks refresh their route's inputs from its preceding solver and freeze each reward provider during policy updates.")
    line("Evaluation and compute","Heading2")
    line("Every variant shares its problem's canonical expression hash. The in-distribution population uses two to four operations and reserves trees with two internal root children. Longer test expressions have five to seven operations. A separate evidence-transfer mutation reverses nonzero sign and increases absolute magnitude, with zero mapped to minus three. Solver and evidence-pair evaluations decode greedily. Natural-review replays and flat ballots sample judgments. Comparisons use identical solver-trace IDs, and the final seal verifies the order of the problems and preceding reports seen during training.")
    if data["budget"]:
        b=data["budget"]
        line(f"The disposable pilot measured {b['seconds_per_update']:.2f} seconds per update. The budget rule selected {b['updates']} updates per block. The wall-clock estimate excludes checkpoint loading. Every registered arm uses this update count.")
    if data["profile"]:
        config=data["profile"]
        line(f"The amended primary population uses {config['family']} arithmetic with {config['style']} prompts for every arm. Learning was measured on a separate validation partition before this population was frozen. The primary comparison uses 2,048 new canonical problems. The following 128 form the evidence cohort. The original signed population is also evaluated for transfer.")
        if config["family"]=="registered":
            line("The signed-difficulty transfer and the amended primary coincide for this selection.")
        elif config["family"]=="one":
            line("The amended primary has one operation per problem, so its final answer is the complete trace. Multi-step evidence comes from the signed, layout and length transfer cohorts.")
        if data["original_development"]:
            table(["Original development","Correct complete trace","Problems"],
                  [[r["name"],r["correct"],r["n"]] for r in data["original_development"]])
    line("Results and interpretation","Heading1")
    for grid in reversed(data["matched_depth"]):
        split = "Development" if grid["phase"]=="development" else "Held-out"
        line(f"{split} accuracy by actual judge depth","Heading2")
        line(f"Solver scores require the complete calculation on {grid['solver_n']} common problems. Judge scores use "
             f"verdict agreement with the checker on {grid['judge_n']} identical saved base-solver responses. Each extra call "
             "reviews its predecessor. Fitted judges stay frozen during solver optimization.")
        table(["Solver training","One judge","Two judges","Three judges"],grid["solver"])
        if grid["solver_note"]:
            line(grid["solver_note"])
        table(["Judge training","One judge","Two judges","Three judges"],grid["judge"])
        line(grid["judge_note"])
    line("Development accuracy for a solver requires every arithmetic step to be correct. For a judge it requires its whole record to match the executable audit. Held-out solver accuracy uses one response per problem. A dash denotes a pending measurement.")
    if data["runs"]:
        table(["Run","Role","Updates","Dev. n","Dev. exact","Test n","Test exact"],
              [[r["name"],r["role"],str(r["updates"] or "—"),str(r["dev_n"]),percent(r["dev"]),str(r["test_n"]),percent(r["test"])] for r in data["runs"]])
    else:
        line("No model observations have been recorded at the protocol milestone.")
    if data["depth_review"]:
        line("How did the third verdict change the training signal?", "Heading2")
        line("This exploratory diagnostic compares Judge 2 and Judge 3 on the identical answers already sampled by the three-judge solver. Each changed group has a different vector of within-question GRPO advantages after substituting Judge 2’s verdict. Re-training changes the answers subsequently sampled by the solver.")
        table(["Seed","Training answers","J3 fixes","J3 harms","Changed groups","Dev. exact D2","Dev. exact D3"],
              [[r["seed"],r["n"],r["fixes"],r["harms"],f"{r['changed_groups']}/{r['groups']}",
                f"{r['two']['dev']['correct']}/{r['dev_n']}",f"{r['three']['dev']['correct']}/{r['dev_n']}"]
               for r in data["depth_review"]])
        line(f"Per-problem verdict changes, reward rates by arithmetic error and within-group preferences are in the <link href='{GITHUB}/blob/main/reports/reviews/depth-diagnosis.md'>depth analysis</link>. It was specified after seeing the first development contrast.")
        first = data["depth_review"][0]
        line(late_rewards(first).replace("**",""))
        examples = differing_examples(first["paired_outputs"])
        if examples:
            pair = examples[0]
            truth = ", ".join(map(str, pair["truth"]))
            line(f"On {pair['expression']}, the exact steps were {truth}. The table gives the literal solution and "
                 "three post-training reports for each solver. Judge 2 and Judge 3 put the solver verdict in field four.")
            story[-1].keepWithNext = True
            table(["Training reward","Solver wrote","Judge 1","Judge 2","Judge 3"],
                  [[f"Judge {d}", out["trace"], *out["reports"]] for d, out in enumerate(pair["outputs"], 2)])
        line(f"<link href='{GITHUB}/blob/main/reports/reviews/paired-outputs-seed-{first['seed']}.md'>Every paired "
             f"development answer and judge report for seed {first['seed']}</link> is available in evaluation order.")
    learning=data["learnability"]
    if learning["screen"]:
        line("Attainable benchmark amendment","Heading2")
        line("A development-only difficulty screen crosses arithmetic complexity with completed chat demonstrations. A separate exact-reward training control tests whether the model improves on fresh problems after optimization. The initial benchmark and the calibrated population keep distinct identities.")
        table(["Family","Prompts","Problems","Parsed","Sample exact","Greedy exact","Mixed groups"],
              [[c["family"],c["style"],c["problems"],percent(c["parsed"]),percent(c["sampled_exact"]),
                percent(c["greedy_exact"]),c["mixed_groups"]] for c in learning["screen"]["cells"]])
        selected=learning["screen"]["selected"]
        line(f"The frozen-model rule selected {selected['family']} with {selected['style']} prompts." if selected else
             "No candidate qualified under the frozen-model selection rule.")
        if learning["learning"]:
            gain=learning["learning"]["over_base"]
            line(f"Exact-reward training changed held-out development accuracy by {100*gain['delta']:+.2f} percentage points relative to the starting solver. The paired 95% interval was [{100*gain['interval'][0]:+.2f}, {100*gain['interval'][1]:+.2f}] points. The full shuffled control is in the learnability report.")
            if "by_parse" in learning["learning"]:
                groups = learning["learning"]["by_parse"]["base"]["groups"]
                table(["Formatting on the same problem","Problems","Gains","Losses"],
                      [[g["stratum"],g["n"],g["gains"],g["losses"]] for g in groups])
                line("A gain when both responses already parse requires a corrected arithmetic trace. A gain in a newly parseable response can combine arithmetic and formatting changes.")
            if data.get("learning_review"):
                audit=data["learning_review"]
                line(f"The replay audit reproduced all {audit['scored']} response grades and both paired intervals. The two training arms shared {audit['training']} unique prompts in identical order. The training, screening, confirmation and validation partitions had {audit['overlap']} shared canonical problem IDs.")
    primary = data["primary"]
    if "delta" in primary:
        line(f"The equally weighted paired difference is {primary['delta']*100:.2f} percentage points. The conditional 95% problem-bootstrap interval is [{primary['ci'][0]*100:.2f}, {primary['ci'][1]*100:.2f}] points. The registered decision is {primary['status']}.")
    comparisons = list(contrast_rows(data))
    if comparisons:
        table(["Contrast", "Seed", "Difference (pp)", "95% lower", "95% upper"], comparisons)
        line("Intervals resample problem identities within the common held-out sample. The pooled contrast weights the three trained seeds equally. The voting contrast is secondary.")
    line("Secondary outcomes","Heading2")
    checks = [r for r in data["runs"] if r["dev_n"]]
    if checks:
        table(["Run","Dev. n","J3 fixes","J3 harms","Twin split","Twin n","Visible pair","Masked pair"],
              [[r["name"],r["dev_n"],r["fixed"],r["harmed"],r["twin_split"] or "—",r["twins_n"],percent(r["twins"]),percent(r["masked"])] for r in checks])
        first=checks[0]
        line(f"For {first['name']}, {first['dev_malformed']} of {first['dev_n']} development responses failed the registered trace format. A secondary, post-hoc parser identified {first['dev_named_correct']} fully correct traces written as named assignments among those failures. These retain their original primary scores.")
        initial = first["replay"][0]
        line(f"On {first['name']}, Judge 1 agreed with the checker on {percent(initial['agreement'])} of solution verdicts. Its entire evidence record was correct on {initial['evidence_correct']} of {initial['n']} traces. Malformed reports default to rejection and occurred on {initial['malformed']} of {initial['reports']} calls. This measurement included {initial['valid']} genuinely valid solver traces.")
        for r in checks[:2]:
            if r["examples"]:
                ex=r["examples"][0]
                shown=escape(ex["trace"]).replace("\n","<br/>")
                line(escape(f"{r['name']}. {ex['expression']}.")+"<br/>Solver output<br/>"+shown+"<br/>"+
                     escape(f"Expected {ex['expected_values']}. Exact acceptance {ex['correct']}."))
    else:
        line("Paired evidence interventions and natural correction counts are pending.")
    natural_test=[r for r in data["runs"] if r["test_review_n"]]
    if natural_test:
        line("Held-out natural reviews","Heading2")
        table(["Run","Traces","J3 fixes","J3 harms","Net verdict change (pp)"],
              [[r["name"],r["test_review_n"],r["test_fixed"],r["test_harmed"],
                f"{100*(r['test_fixed']-r['test_harmed'])/r['test_review_n']:+.2f}"] for r in natural_test])
    unique_reviewers=[r for r in data["runs"] if (r["name"]=="base" or r["role"]=="j3") and r["twins_n"]]
    if unique_reviewers:
        line("Which parts of the review were correct?","Heading2")
        field_rows=[]
        for r in unique_reviewers:
            for mode, counts in r["evidence_fields"].items():
                field_rows.append([r["name"],r["twin_split"],mode,counts["reports"],counts["parsed"],
                                   counts["solution_bit"],counts["audit_bit"],f"{counts['localized_and_repaired']}/{counts['faults']}"])
        table(["Reviewer","Split","Evidence","Reports","Parsed","Solution bit","Audit bit","Fault repaired"],field_rows)
        line("The first two accuracy counts award one for the correct decision on the solver or preceding reviewer, respectively. Fault repair requires rejecting the altered review and giving both its first incorrect field and the exact replacement. An unparseable six-field report earns zero on these measures. Each frozen reviewer appears once.")
    transferred=[r for r in unique_reviewers if r["transfer_twin_n"]]
    if transferred:
        line("Evidence transfer","Heading2")
        table(["Reviewer","Familiar both","Novel error","Novel layout","Both novel","Pairs per cell"],
              [[r["name"],percent(r["twins"]),percent(r["unseen_evidence"]["visible"]),
                percent(r["layout_evidence"]["visible"]),percent(r["transfer_visible"]),r["transfer_twin_n"]] for r in transferred])
    solver_transfer = [r for r in data["runs"] if r["role"]=="solver" and r["test_n"] and data["profile"]]
    if solver_transfer:
        line("Solver transfer","Heading2")
        table(["Run","Primary","Original difficulty","Unseen layout","Longer expressions"],
              [[r["name"],percent(r["test"]),percent(r["test"] if data["profile"]["family"]=="registered" else r["transfer"]["original-difficulty"]),
                percent(r["transfer"]["layout"]),percent(r["transfer"]["long"])] for r in solver_transfer])
    cost_rows=[]
    for r in data["runs"]:
        if r["seed"]==17 and r["name"] in ("d1-17","d2-17","d3-17","flat-17","oracle-17","hybrid-17","shuffle-17") and r["usage"]:
            reward_calls=[v for k,v in r["usage"].items() if k in ("j1","j2","j3","flat_j1")]
            cost_rows.append([r["name"], r["zero_groups"], r["groups"],
                              *(sum(v[k] for v in reward_calls) for k in ("calls","input_tokens","output_tokens")),
                              f"{sum(v['gpu_seconds'] for v in reward_calls):.1f}"])
    if cost_rows:
        line("Reward signal and generation cost","Heading2")
        table(["Run","Constant groups","Groups","Judge calls","Input tokens","Output tokens","CUDA seconds"],cost_rows)
        line("Counts cover reward-provider calls during training. CUDA events span batched generation and can include device idle time between kernel submissions. The flat panel and recursive chain share a call count and output ceiling. Their prompt lengths and stopping lengths may differ.")
    for filename, caption in (("learnability.png","Solver learnability on fresh validation problems"),("paired-outcomes.png","Seed-specific and pooled held-out effects"),("outcomes.png","Development complete-trace accuracy"),("examples.png","Common problem across methods"),("depth-trajectory.png","Exact arithmetic and assigned rewards during two-judge and three-judge solver training"),("training.png","Frozen three-judge solver training")):
        asset=DOCS/"assets"/filename
        if asset.exists():
            from reportlab.lib.utils import ImageReader
            w,h=ImageReader(str(asset)).getSize()
            width=min(160*mm,105*mm*w/h)
            line(caption,"Heading3")
            story.append(Image(str(asset),width=width,height=width*h/w))
    line("Discussion, limitations and conclusion","Heading2")
    line("Only a paired comparison on sealed arithmetic problems can establish the registered solver effect. A higher training reward can coexist with lower exact accuracy [6]. The same underlying model supplies all three reviewers, so their errors may be correlated. Compact evidence records make audits decidable but leave unrestricted prose and other model families outside the tested population. Interval estimates condition on the trained checkpoints. Seed-specific estimates describe variation across the registered runs.")
    story.append(PageBreak())
    line("Run inventory","Heading1")
    line(GUIDE)
    if data["online_solvers"]:
        line("Original solver trained with frozen Qwen3.5-4B judges","Heading2")
        table(*online_report.score_table(data["online_solvers"]))
        line(escape(online_report.conclusion(data["online_solvers"])))
    if data["newer_judges"]["results"]:
        line("Frozen Qwen verdict and evidence scores", "Heading2")
        chart=DOCS/"assets/frozen-judge-scores.png"
        if chart.is_file():
            image=Image(str(chart))
            image.drawHeight=image.imageHeight*165*mm/image.imageWidth
            image.drawWidth=165*mm
            story.append(image)
        for values in frozen_rows(data["newer_judges"]):
            name,*scores = values
            line(escape(f"{name}. J1, J2 and J3 verdict scores were {', '.join(scores[:3])}. Visible and masked whole-pair scores were {', '.join(scores[3:5])}. Judge 3 fixes / new errors relative to Judge 2 were {scores[5]}."))
        for r in data["newer_judges"]["results"]:
            if not r.get("metrics"):
                line(escape(f"{r['model']}: {r['result']}."))
        for finding in interpretation(data["newer_judges"]):
            line(escape(finding))
    line(f"Model sizes, pinned weights, inclusion rules and the separate follow-up protocol are available in the <link href='{GITHUB}/blob/main/reports/newer-frozen-judges.md'>newer frozen judge protocol</link>. The calibrated final assessment includes paired depth and flat-vote contrasts, signed-difficulty, layout and length transfer, natural verdict changes and visible/masked evidence interventions.")
    from reportlab.lib.styles import ParagraphStyle
    small = ParagraphStyle("InventoryCell", parent=styles["BodyText"], fontSize=7.6, leading=9.6, spaceBefore=0, spaceAfter=0)
    for group, records in grouped(data["inventory"]):
        line(group, "Heading2")
        body = [[Paragraph(escape(str(v)),small) for v in values] for values in (
            HEADERS, *([r["id"],r["treatment"],r["status"],r["result"],r["held_out"]] for r in records))]
        ledger_table = Table(body, colWidths=[35*mm,49*mm,29*mm,32*mm,22*mm], repeatRows=1, hAlign="LEFT")
        ledger_table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#dceeea")),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#f5f7f6")]),("VALIGN",(0,0),(-1,-1),"TOP")]))
        story.append(ledger_table)
    line("Appendix and references","Heading2")
    line(f"The published protocol, run matrix, role prompts, raw per-problem outputs and analysis code are available in the <link href='{GITHUB}'>study repository</link>. The registered practical threshold is three percentage points, evaluated on 2,048 paired IDs with 10,000 paired bootstrap resamples after all three seeds complete.")
    for title,url in [("[1] Wen et al. Recursive Self-Critiquing","https://arxiv.org/abs/2502.04675"),
                      ("[2] DeepSeekMath-V2","https://arxiv.org/abs/2511.22570"),
                      ("[3] Stojanovski et al. Reasoning Gym","https://arxiv.org/abs/2505.24760"),
                      ("[4] Zheng et al. ProcessBench","https://arxiv.org/abs/2412.06559"),
                      ("[5] Shao et al. DeepSeekMath","https://arxiv.org/abs/2402.03300"),
                      ("[6] Huang et al. From Accuracy to Robustness","https://arxiv.org/abs/2505.22203"),
                      ("[7] Qwen2.5-1.5B-Instruct, immutable checkpoint","https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct/tree/989aa7980e4cf806f80c7fef2b1adb7bc71aa306"),
                      ("[8] Hugging Face TRL, GRPO trainer","https://huggingface.co/docs/trl/grpo_trainer"),
                      ("[9] Hugging Face PEFT, quantization and adapter training","https://huggingface.co/docs/peft/developer_guides/quantization")]:
        line(f"<link color='#17665b' href='{url}'>{title}</link>")
    line("AI statement","Heading3")
    line("Codex wrote this codebase and paper. A human provided the exact specification that Codex executed. Human cleanup and rewriting are in progress.")
    def footer(canvas, doc):
        canvas.setFont("StudySans",8)
        canvas.drawRightString(191*mm,12*mm,str(doc.page))
    SimpleDocTemplate(str(REPORTS/"paper.pdf"),pagesize=A4,leftMargin=20*mm,rightMargin=20*mm,
                      topMargin=17*mm,bottomMargin=20*mm,title="Does a third LLM judge improve GRPO rewards?",
                      author="Libor “Burny” Burian",invariant=1).build(story,onFirstPage=footer,onLaterPages=footer)


def build():
    online_report.verify_pair(ORIGINAL_RESULTS)
    data = collect()
    final_review = review_completed(ORIGINAL_RESULTS,data)
    review_path = REPORTS/"reviews/final.md"
    if final_review:
        atomic(review_path,final_review_text(final_review))
    else:
        review_path.unlink(missing_ok=True)
    scoped = ORIGINAL_RESULTS / ("calibrated" if data["profile"] else "")
    data["depth_review"] = collect_depth_review(scoped, data["profile"])
    depth_file = REPORTS/"reviews/depth-diagnosis.md"
    if data["depth_review"]:
        atomic(depth_file,depth_review_text(data["depth_review"]))
        for review in data["depth_review"]:
            atomic(REPORTS/"reviews"/f"paired-outputs-seed-{review['seed']}.md", paired_text(review))
    else:
        depth_file.unlink(missing_ok=True)
    data["learning_review"] = check_release(ORIGINAL_RESULTS)
    review_file = REPORTS/"reviews/learning-control.md"
    if data["learning_review"]:
        atomic(review_file,review_text(data["learning_review"]))
    else:
        review_file.unlink(missing_ok=True)
    date = datetime.now(ZoneInfo("Europe/Berlin")).date().isoformat()
    figures(data)
    write_json(DOCS/"assets/study.json", data)
    score = scores_table(data)
    primary = data["primary"]
    atomic(REPORTS/"learnability.md",learnability_text(data["learnability"]))
    profile = data["profile"]
    prefix = "calibrated/" if profile else ""
    source = ORIGINAL_RESULTS / prefix
    status = ("Amended primary comparison" if profile else "Registered primary comparison")+" is "+primary["status"]+"."
    if profile:
        status += f" Every arm uses {profile['family']} problems and {profile['style']} prompts."
    if "delta" in primary:
        status += f" Difference {100*primary['delta']:.2f} percentage points, conditional 95% interval [{100*primary['ci'][0]:.2f}, {100*primary['ci'][1]:.2f}]."
    summary = status+"\n\n"+score
    if data["depth_review"]:
        summary += f"\n\n[How the third judge changed actual training rewards and worked examples]({GITHUB}/blob/main/reports/reviews/depth-diagnosis.md)."
        seed = data["depth_review"][0]["seed"]
        summary += f" [Side-by-side solver outputs and judge reports]({GITHUB}/blob/main/reports/reviews/paired-outputs-seed-{seed}.md)."
    if final_review:
        summary += f"\n\n[Independent rescoring, split checks and paired outcomes against one, two and three independent judges]({GITHUB}/blob/main/reports/reviews/final.md)."
    learning = data["learnability"]
    if learning["screen"]:
        chosen = learning["screen"]["selected"]
        if chosen:
            summary += (f"\n\n**Benchmark difficulty.** The frozen-model screen selected {chosen['family']} with {chosen['style']} prompts. "
                        f"On {chosen['problems']} screening problems it produced a mix of correct and incorrect answers on "
                        f"{chosen['mixed_groups']} problems. [All difficulty levels](reports/learnability.md).")
        else:
            summary += "\n\n**Benchmark difficulty.** No setting passed the registered difficulty screen. [All difficulty levels](reports/learnability.md)."
    if learning["learning"]:
        change=learning["learning"]["over_base"]
        summary += (f"\n\n**Solver learning.** Exact-reward training changed complete-trace accuracy on {change['n']} fresh "
                    f"problems by {100*change['delta']:+.1f} percentage points relative to the starting solver "
                    f"(paired 95% interval {100*change['interval'][0]:+.1f} to {100*change['interval'][1]:+.1f}). "
                    "[Shuffled control and arithmetic corrections](reports/learnability.md).")
    if data["original_development"]:
        summary += "\n\nOn the original signed development population, "+", ".join(
            f"{r['name']} solved {r['correct']}/{r['n']}" for r in data["original_development"])+"."
    for run in data["runs"]:
        if run["name"] in ("base","d3-17") and run["completed_development"]:
            label = "Untrained solver" if run["name"]=="base" else "First three-judge-trained solver"
            summary += (f"\n\n**{label}.** Every step was correct on {run['dev_correct_n']} of {run['dev_n']} development problems. "
                        f"Of {run['dev_malformed']} malformed outputs, {run['dev_named_correct']} contained all correct numbers as named assignments. "
                        f"Judge 3 corrected {run['fixed']} of Judge 2’s verdicts and introduced {run['harmed']} errors on these traces.")
    comparisons = list(contrast_rows(data))
    if comparisons:
        summary += "\n\n" + markdown(["Contrast", "Seed", "Difference (pp)", "95% lower", "95% upper"], comparisons)
    explanation = "Solver scores require every intermediate value. Judge scores require all fields of the evidence record. Intervals condition on the trained checkpoints."
    grid_text = grid_markdown(data["matched_depth"])
    trajectory_note = ""
    if data["depth_review"]:
        first = data["depth_review"][0]
        trajectory_note = (f"\n\n### Reward and arithmetic during training, seed {first['seed']}\n\n"
                           +late_rewards(first)+
                           f" [All four quarters, denominators and original records]({GITHUB}/blob/main/reports/reviews/depth-diagnosis.md).")
    ledger = inventory_markdown(data["inventory"])
    frozen_summary = frozen_text(data["newer_judges"])
    headline = confirmation_headline(data['newer_judges'])
    highlight = f"**Independent frozen-judge confirmation.** {headline}\n\n" if headline else ""
    online_summary = online_report.online_text(data["online_solvers"])
    highlight = online_summary + highlight
    if data['newer_judges'].get('review'):
        atomic(REPORTS/'reviews/frozen-confirmation.md',confirmation_review_text(data['newer_judges']))
        frozen_summary += f"\n\n[Case identities, selection and interval audit]({GITHUB}/blob/main/reports/reviews/frozen-confirmation.md)."
    frozen_chart = (f"\n\n![Frozen verdict and whole-pair accuracy]({GITHUB}/raw/refs/heads/main/docs/assets/frozen-judge-scores.png)"
                    if (DOCS/"assets/frozen-judge-scores.png").is_file() else "")
    frozen_summary += frozen_chart
    experiment_pages(data["newer_judges"], REPORTS/"experiments/new-judges")
    online_report.experiment_pages(data["online_solvers"], REPORTS/"experiments/new-judges")
    atomic(REPORTS/"experiments/new-judges/experiment.md", frozen_summary+"\n\n[Protocol and case selection](../../newer-frozen-judges.md).\n")
    findings = interpretation(data["newer_judges"])
    if findings:
        atomic(REPORTS/"experiments/new-judges/learnings.md", "# Findings on frozen judge releases\n\n"+
               "\n\n".join(findings)+"\n\n[All scored runs and costs](experiment.md) · [Protocol](../../newer-frozen-judges.md).\n")
    ledger_links = (f"[Run inventory, including upcoming experiments]({GITHUB}/blob/main/reports/run-inventory.md) · "
                    f"[Newer frozen Qwen protocol]({GITHUB}/blob/main/reports/newer-frozen-judges.md)")
    paused = read_json(ORIGINAL_RESULTS/"calibrated/top-depth2/resume-checkpoint.json", {})
    if paused:
        ledger_links += (f" · [Paused solver checkpoint, update {paused['checkpoint_step']}]"
                         f"(https://huggingface.co/{paused['repo']}/tree/{paused['revision']}/{paused['path']})")
    atomic(REPORTS/"run-inventory.md","# Run inventory\n\n"+ledger+"\n\n"+ledger_links+"\n")
    atomic(REPORTS/"summary.md","# Study summary\n\n"+highlight+ledger_links+"\n\n"+grid_text.replace("(reports/matched-depth-protocol.md)","(matched-depth-protocol.md)")+
           summary.replace("(reports/learnability.md)","(learnability.md)")+trajectory_note+"\n\n"+explanation+" [Preregistration](preregistration.md).\n\n"+frozen_summary+"\n\n## Run inventory\n\n"+ledger+"\n")
    readme = (ROOT/"README.md").read_text(encoding="utf-8")
    pre, tail = readme.split("<!-- RESULTS:START -->",1)
    _, post = tail.split("<!-- RESULTS:END -->",1)
    assets = "![Study architecture](docs/assets/architecture.png)\n\n"
    if (DOCS/"assets/learnability.png").exists():
        assets += "![Learning validation for the exact-reward and shuffled controls](docs/assets/learnability.png)\n\n"
    if "delta" in primary:
        assets += "![Conditional paired held-out effects](docs/assets/paired-outcomes.png)\n\n"
    if (DOCS/"assets/outcomes.png").exists():
        assets += "![Development solver accuracy](docs/assets/outcomes.png)\n\n"
    if (DOCS/"assets/examples.png").exists():
        assets += "![Model outputs and exact labels on a common development problem](docs/assets/examples.png)\n\n"
    completed_dev = {r["name"] for r in data["runs"] if r["completed_development"]}
    completed_final = {r["name"] for r in data["runs"] if r["completed_final"]}
    schedule = matrix(profile)
    milestones = [
        ("Complete the frozen-judge solver comparison.", all(r.name in completed_dev for r in schedule if r.name.rsplit("-",1)[-1].isdigit())),
        ("Evaluate Judge 3 on natural reviews and paired evidence changes.", {"base","exact-j3","alt-exact-j3","alt-top-j3"} <= completed_final),
        ("Compare exact and top-down judge supervision and alternating training.", all(r.name in completed_dev for r in schedule if not r.name.rsplit("-",1)[-1].isdigit())),
        ("Release complete paired held-out results, positive and negative examples, and the reproducible analysis.",
         data["completed"] and "delta" in primary)]
    for label, done in milestones:
        marker="- [x] " if done else "- [ ] "
        post=post.replace("- [ ] "+label,marker+label).replace("- [x] "+label,marker+label)
    diagnostic = readme_depth(data)
    if diagnostic:
        diagnostic += "## Study results\n\n"
    inline_inventory = ("<details>\n<summary>All runs, their results, and what is still scheduled</summary>\n\n"+ledger+"\n\n</details>\n\n")
    atomic(ROOT/"README.md",pre+"<!-- RESULTS:START -->\n"+highlight+ledger_links+"\n\n"+inline_inventory+grid_text+frozen_summary+"\n\n"+diagnostic+assets+summary+f"\n\n[Interactive results explorer]({PAGES}) · [Paper](reports/paper.pdf)\n<!-- RESULTS:END -->"+post)
    experiments=REPORTS/"experiments"
    notes=[]
    methods=[]
    for r in data["runs"]:
        sub = "" if r["diagnostic"] else prefix
        directory = experiments/sub/r["name"]
        up = "../" if sub else ""
        observations=[]
        pilot_validation = learning["evaluations"].get(r["name"]) if r["diagnostic"] else None
        validation_text = ""
        if pilot_validation:
            e=pilot_validation
            observation=(f"On the fresh learning-validation cohort, {e['correct']} of {e['n']} complete traces "
                         f"were correct and {e['parsed']} parsed.")
            observations.append(observation)
            validation_text=f"\n\n{observation} [Individual validation records](../../../results/learnability/evaluations/{r['name']}.jsonl)."
        if r["groups"]:
            observations.append(f"The exact checker accepted {percent(r['train_exact'])} of observed policy outputs. "
                                f"The assigned reward averaged {percent(r['train_reward'])}. Of {r['observations']} rollouts, "
                                f"{r['positive_on_incorrect']} received reward for an incorrect output and {r['zero_on_correct']} lost reward for a correct output. "
                                f"{r['zero_groups']} of {r['groups']} complete groups had identical rewards.")
        if r["dev_n"]:
            if r["role"]=="solver":
                observations.append(f"The solver completed {r['dev_correct_n']} of {r['dev_n']} development calculations exactly. "
                                    f"Among {r['dev_malformed']} serialization failures, {r['dev_named_correct']} contained all correct numbers as named assignments.")
            else:
                observations.append(f"The updated reviewer gave an entirely correct decision and evidence record on {percent(r['dev'])} of {r['dev_n']} natural development traces.")
            observations.append(f"On those same development traces, Judge 3 fixed {r['fixed']} of Judge 2’s verdicts and introduced {r['harmed']} errors.")
        obs=" ".join(observations) or "The first complete observation is pending."
        meta = training_method(r)
        meta+=f" The shared architecture, optimizer and sample definition are in the [registered protocol]({up}../../preregistration.md)."
        coverage = None
        if r["dev_n"]:
            malformed = r["dev_malformed"] if r["role"]=="solver" else r["replay"][int(r["role"][1:])-1]["malformed"]
            coverage=1-malformed/r["dev_n"]
        methods.append([r["name"],r["role"],r["reward"],r["seed"],"arithmetic" if r["role"]=="solver" else r["corpus"],
                        percent(coverage),percent(r["dev"]),percent(r["test"])])
        atomic(directory/"experiment.md",f"# {sub}{r['name']}\n\n{meta}\n\n{scores_table({'runs':[r]})}{validation_text}\n\n{run_evidence(r)}\n\n[Machine observations]({up}../../../results/{sub}{r['name']})\n")
        atomic(directory/"learnings.md",f"# Observations from {sub}{r['name']}\n\n{obs}\n\n[Raw measurements and denominators](experiment.md) · [Analysis amendments]({up}../../amendments.md)\n")
        notes.append(f"- [{sub}{r['name']}]({sub}{r['name']}/learnings.md). {obs}")
    references="\n".join(f"- [{r['name']}]({'' if r['diagnostic'] else prefix}{r['name']}/experiment.md)" for r in data["runs"])
    references+="".join(f"\n- [Original {r['name']}]({r['name']}/experiment.md)" for r in data["original_development"])
    methods_table=markdown(["Run","Role","Reward","Seed","Problem source","Dev. parsed","Dev. exact","Held-out exact"],methods)
    atomic(experiments/"experiments.md","# Experiment index\n\n"+online_summary+ledger_links+"\n\nAll learned models use grouped reinforcement learning with one active LoRA adapter on the shared, quantized Qwen2.5-1.5B-Instruct backbone. The solver predicts values in signed-integer expression trees. Judges predict exact evidence records about earlier outputs. A parsed output supplies the required number of integers. An exact output also gets every field right.\n\n"+methods_table+"\n\n[Update counts and sample sizes](../summary.md) · [Objectives and curricula](../planned-runs.md) · [Analysis protocol](../preregistration.md)\n\n"+references+"\n")
    link_to_findings = "[Frozen judge comparisons and independent confirmation](new-judges/learnings.md).\n\n" if findings else ""
    atomic(experiments/"learnings.md","# Experimental learnings\n\n"+online_summary+link_to_findings+("\n".join(notes) or "No experimental observations yet.")+"\n")
    core=[r for r in data["runs"] if r["name"]!="base" and not r["diagnostic"] and not r["supplemental"]]
    complete=sum(r["completed_final"] for r in core)
    trained=sum(r["updates"] is not None for r in core)
    activity = [online_summary.rstrip(), ledger_links] if online_summary else [ledger_links]
    operations=read_json(ORIGINAL_RESULTS/"run-snapshot.json",{})
    if operations.get("campaign")=="deferred":
        activity.append(operations["reason"])
        for entry in data["inventory"]:
            if entry["status"].startswith("Paused"):
                activity.append(entry["id"]+" · "+entry["status"]+".")
        activity.append(frozen_summary)
    if profile:
        extra=[r for r in data["runs"] if r["supplemental"]]
        activity.append(f"The matched-depth extension has trained {sum(r['updates'] is not None for r in extra)} "
                        f"of {len(MATCHED_NAMES)} additional shallow solvers. [Extension](matched-depth-protocol.md).")
    if data["budget"]:
        b = data["budget"]
        activity.append(f"The timing pilot selected {b['updates']} updates per block at {b['seconds_per_update']:.1f} seconds per pilot update. A block at that rate would take {b['updates']*b['seconds_per_update']/3600:.2f} hours.")
        for r in data["runs"]:
            root = ORIGINAL_RESULTS if r["diagnostic"] else source
            recipe = read_json(root/r["name"]/"recipe.json", {})
            if r["name"]!="base" and r["updates"] is None and recipe and operations.get("campaign")!="deferred":
                activity.append(f"{r['name']} has scored {r['groups']} complete rollout groups against its target of {recipe['updates']}. The live dashboard reads incoming observations between releases.")
    atomic(REPORTS/"progress.md",f"# Progress · {date}\n\n{trained} of {data['planned']} registered training blocks have completed. {complete} have completed final evaluation. {status}\n\n"+"\n\n".join(activity)+"\n\nThe first single-seed solver has a 14-hour target. The matrix has a one-week training target. Monitoring cadence and milestone order are in the [plan](plan.md). The [experiment index](experiments/experiments.md) contains available development observations.\n")
    paper(data,date)
    return data
