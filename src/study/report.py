"""Rebuild all public numbers from complete observations and attach denominators."""

from collections import defaultdict
from datetime import datetime
from math import sqrt
from statistics import NormalDist, mean
from zoneinfo import ZoneInfo

from .analysis import paired_comparison, paired_primary, replay_metrics
from .design import matrix
from .records import named_values
from .storage import RESULTS, ROOT, atomic, read_json, rows, write_json
from .tables import contrast_rows, markdown, rate as percent, run_evidence

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
    manifest = {r.name: r for r in matrix()}
    runs, outcomes = [], {}
    for name in ("base", *manifest):
        target = RESULTS / name
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
        runs.append(dict(name=name, role=role, reward=spec.reward if spec else "untrained",
                         seed=spec.seed if spec else 17, updates=trained.get("updates"), observations=len(training),
                         train_exact=fraction(training,"label"), train_reward=fraction(training,"reward"),
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
                         transfer_twin_n=len(transfer_twins), transfer_visible=fraction(transfer_twins,"visible_pair"),
                         transfer_masked=fraction(transfer_twins,"masked_pair"),
                         unseen_evidence=dict(n=len(unseen_twins),visible=fraction(unseen_twins,"visible_pair"),masked=fraction(unseen_twins,"masked_pair")),
                         layout_evidence=dict(n=len(layout_twins),visible=fraction(layout_twins,"visible_pair"),masked=fraction(layout_twins,"masked_pair")),
                         evidence_sources=(final or read_json(target/"development.json",{})).get("evidence_sources",{}),
                         twin_split=twins[0]["split"] if twins else None, paired_example=twins[0] if twins else None,
                         replay=replay_metrics(dev), curves=curves, logs=reports, examples=examples, common_example=common_example,
                         usage=trained.get("usage", {}), elapsed_seconds=trained.get("elapsed_seconds"),
                         transfer={s: fraction(list(rows(target/(s+".jsonl"))), "correct") for s in ("layout","long")} if final else {},
                         completed_final=bool(final), completed_development=(target/"development.json").is_file()))
    return dict(runs=runs, primary=paired_primary(outcomes), flat=paired_comparison(outcomes,"flat"), planned=len(manifest),
                budget=read_json(RESULTS/"budget.json"), sealed=(RESULTS/"seal.json").is_file())


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
    ax.text(.12,.25,"The exact checker verifies each stated claim. The last solution verdict supplies the solver reward.",
            fontsize=10, color=colors[0])
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


def paper(data, date):
    from xml.sax.saxutils import escape
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    styles = getSampleStyleSheet()
    story = []
    def line(text, style="BodyText"):
        paragraph = Paragraph(text, styles[style])
        if style.startswith("Heading"):
            paragraph.keepWithNext = True
        story.append(paragraph)
    def table(headers, body):
        t = Table([headers,*body], repeatRows=1, hAlign="LEFT")
        t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#dceeea")),
                               ("FONTSIZE",(0,0),(-1,-1),8.5),("VALIGN",(0,0),(-1,-1),"TOP"),
                               ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#f5f7f6")])]))
        story.extend([Spacer(1,2*mm),t,Spacer(1,2*mm)])
    line("Does a third LLM judge improve GRPO rewards?", "Title")
    line("Libor “Burny” Burian · "+date, "Heading3")
    line("Abstract","Heading2")
    line("A solver submits an integer calculation trace. Three successive language-model calls grade the trace, audit the first judgment and audit the second judgment. An independent integer checker can evaluate every field. We test the incremental effect of the third review on online GRPO and its ability to detect an evidence-only error in another judge's report. The registered primary comparison currently has status <b>"+data["primary"]["status"]+"</b>.")
    line("Motivation and related work","Heading2")
    line("Wen et al. studied third-order pairwise critique and reward-model-guided best-of-N selection [1]. DeepSeekMath-V2 used a learned meta-verifier to review identified proof defects [2]. Our intervention uses the terminal solution verdict as an online policy reward and tests the review itself through an exact counterfactual. Comparing a chain with three independent votes measures the contribution of reviewing previous claims at a comparable generation budget.")
    story.append(Image(str(DOCS/"assets/architecture.png"), width=164*mm, height=37*mm))
    line("Methods","Heading2")
    line("The Reasoning Gym-derived sampler produces signed-integer expression trees [3]. Each operation has a numbered result. A report names the first erroneous step and its correction, following the first-error formulation used by ProcessBench [4]. An audit identifies the first erroneous field in the previous report, its replacement, and the final verdict on the original solution. A correct final value with a wrong intermediate step fails the complete-trace metric.")
    line("Policies share the pinned Qwen2.5-1.5B-Instruct backbone and use separate NF4/LoRA role configurations. GRPO uses four samples per prompt, group-scaled rewards, a clipped ratio, and a zero KL coefficient [5]. Solver-only, judge-only and alternating stages isolate which component learns. The control arms use depth one, depth two, a three-vote panel, exact outcomes, exact-gated learned rewards, and within-group shuffled rewards.")
    story.append(PageBreak())
    line("Results and interpretation","Heading1")
    line("Development accuracy for a solver requires every arithmetic step to be correct. For a judge it requires its whole record to match the executable audit. Held-out solver accuracy uses one response per problem. A dash denotes a pending measurement.")
    if data["runs"]:
        table(["Run","Role","Updates","Dev. n","Dev. exact","Test n","Test exact"],
              [[r["name"],r["role"],str(r["updates"] or "—"),str(r["dev_n"]),percent(r["dev"]),str(r["test_n"]),percent(r["test"])] for r in data["runs"]])
    else:
        line("No model observations have been recorded at the protocol milestone.")
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
        table(["Run","Natural n","J3 fixes","J3 harms","Twin n","Visible pair","Masked pair"],
              [[r["name"],r["dev_n"],r["fixed"],r["harmed"],r["twins_n"],percent(r["twins"]),percent(r["masked"])] for r in checks])
        first=checks[0]
        line(f"For {first['name']}, {first['dev_malformed']} of {first['dev_n']} development responses failed the registered trace format. A secondary, post-hoc parser identified {first['dev_named_correct']} fully correct traces written as named assignments among those failures. These retain their original primary scores.")
        initial = first["replay"][0]
        line(f"On the frozen baseline, Judge 1 agreed with the checker on {percent(initial['agreement'])} of solution verdicts. Its entire evidence record was correct on {initial['evidence_correct']} of {initial['n']} traces. Malformed reports default to rejection and occurred on {initial['malformed']} of {initial['reports']} calls. This measurement included {initial['valid']} genuinely valid solver traces.")
        for r in checks[:2]:
            if r["examples"]:
                ex=r["examples"][0]
                line(escape(f"{r['name']}. {ex['expression']}. Solver output {ex['trace']!r}. Expected {ex['expected_values']}. Exact acceptance {ex['correct']}." ))
    else:
        line("Paired evidence interventions and natural correction counts are pending.")
    for filename, caption in (("paired-outcomes.png","Seed-specific and pooled held-out effects"),("outcomes.png","Development complete-trace accuracy"),("examples.png","Common problem across methods"),("training.png","Frozen three-judge solver training")):
        asset=DOCS/"assets"/filename
        if asset.exists():
            from reportlab.lib.utils import ImageReader
            w,h=ImageReader(str(asset)).getSize()
            width=min(160*mm,105*mm*w/h)
            line(caption,"Heading3")
            story.append(Image(str(asset),width=width,height=width*h/w))
    line("Discussion, limitations and conclusion","Heading2")
    line("Only a paired comparison on sealed arithmetic problems can establish the registered solver effect. A higher training reward can coexist with lower exact accuracy [6]. The same underlying model supplies all three reviewers, so their errors may be correlated. Compact evidence records make audits decidable but leave unrestricted prose and other model families outside the tested population. Interval estimates condition on the trained checkpoints. Seed-specific estimates describe variation across the registered runs.")
    line("Appendix and references","Heading2")
    line("The tagged protocol, run matrix, role prompts, raw per-problem outputs and analysis code are available in the <link href='https://github.com/BurnyCoder/verifying-verifier-s-verifier-llm-reinforcement-learning'>study repository</link>. The registered practical threshold is three percentage points, evaluated on 2,048 paired IDs with 10,000 paired bootstrap resamples after all three seeds complete.")
    for title,url in [("[1] Wen et al. Recursive Self-Critiquing","https://arxiv.org/abs/2502.04675"),
                      ("[2] DeepSeekMath-V2","https://arxiv.org/abs/2511.22570"),
                      ("[3] Stojanovski et al. Reasoning Gym","https://arxiv.org/abs/2505.24760"),
                      ("[4] Zheng et al. ProcessBench","https://arxiv.org/abs/2412.06559"),
                      ("[5] Shao et al. DeepSeekMath","https://arxiv.org/abs/2402.03300"),
                      ("[6] Huang et al. From Accuracy to Robustness","https://arxiv.org/abs/2505.22203")]:
        line(f"<link color='#17665b' href='{url}'>{title}</link>")
    line("AI statement","Heading3")
    line("Codex wrote this codebase and paper. A human provided the exact specification that Codex executed. Human cleanup and rewriting are in progress.")
    def footer(canvas, doc):
        canvas.setFont("Helvetica",8)
        canvas.drawRightString(191*mm,12*mm,str(doc.page))
    SimpleDocTemplate(str(REPORTS/"paper.pdf"),pagesize=A4,leftMargin=20*mm,rightMargin=20*mm,
                      topMargin=17*mm,bottomMargin=20*mm,title="Does a third LLM judge improve GRPO rewards?",
                      author="Libor Burian",invariant=1).build(story,onFirstPage=footer,onLaterPages=footer)


def build():
    data = collect()
    date = datetime.now(ZoneInfo("Europe/Berlin")).date().isoformat()
    figures(data)
    write_json(DOCS/"assets/study.json", data)
    score = scores_table(data)
    primary = data["primary"]
    status = "Registered primary comparison: "+primary["status"]+"."
    if "delta" in primary:
        status += f" Difference {100*primary['delta']:.2f} percentage points, conditional 95% interval [{100*primary['ci'][0]:.2f}, {100*primary['ci'][1]:.2f}]."
    summary = status+"\n\n"+score
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
    atomic(REPORTS/"summary.md","# Study summary\n\n"+summary+"\n\n"+explanation+" [Preregistration](preregistration.md).\n")
    readme = (ROOT/"README.md").read_text(encoding="utf-8")
    pre, tail = readme.split("<!-- RESULTS:START -->",1)
    _, post = tail.split("<!-- RESULTS:END -->",1)
    assets = "![Study architecture](docs/assets/architecture.png)\n\n"
    if "delta" in primary:
        assets += "![Conditional paired held-out effects](docs/assets/paired-outcomes.png)\n\n"
    if (DOCS/"assets/outcomes.png").exists():
        assets += "![Development solver accuracy](docs/assets/outcomes.png)\n\n"
    if (DOCS/"assets/examples.png").exists():
        assets += "![Model outputs and exact labels on a common development problem](docs/assets/examples.png)\n\n"
    atomic(ROOT/"README.md",pre+"<!-- RESULTS:START -->\n"+assets+summary+"\n\n[Interactive results explorer](https://burnycoder.github.io/verifying-verifier-s-verifier-llm-reinforcement-learning/) · [Paper](reports/paper.pdf)\n<!-- RESULTS:END -->"+post)
    experiments=REPORTS/"experiments"
    notes=[]
    for r in data["runs"]:
        obs=(f"Exact agreement on the recorded training outputs was {percent(r['train_exact'])}. "
             f"The assigned reward averaged {percent(r['train_reward'])}. "
             f"{r['zero_groups']} of {r['groups']} complete groups had identical rewards.") if r["groups"] else "Training observations are pending or this is a frozen evaluation."
        meta=f"Role {r['role']}. Reward {r['reward']}. Seed {r['seed']}. The fixed architecture, curriculum, optimizer and sample definition are in the [registered protocol](../../preregistration.md)."
        atomic(experiments/r["name"]/"experiment.md",f"# {r['name']}\n\n{meta}\n\n{scores_table({'runs':[r]})}\n\n{run_evidence(r)}\n\n[Machine observations](../../../results/{r['name']})\n")
        atomic(experiments/r["name"]/"learnings.md",f"# Observations from {r['name']}\n\n{obs}\n\nNatural reviews corrected {r['fixed']} and introduced {r['harmed']} solution errors among {r['dev_n']} development traces. This is a within-trace comparison.\n")
        notes.append(f"- [{r['name']}]({r['name']}/learnings.md). {obs}")
    references="\n".join(f"- [{r['name']}]({r['name']}/experiment.md)" for r in data["runs"])
    atomic(experiments/"experiments.md","# Experiment index\n\n"+score+"\n\nA complete trace has every intermediate integer correct. Judge accuracy requires the full evidence and decision record. [Architecture, objectives and curricula](../planned-runs.md)\n\n"+references+"\n")
    atomic(experiments/"learnings.md","# Experimental learnings\n\n"+("\n".join(notes) or "No experimental observations yet.")+"\n")
    complete=sum(r["completed_final"] for r in data["runs"] if r["name"]!="base")
    trained=sum(r["updates"] is not None for r in data["runs"])
    activity = []
    if data["budget"]:
        b = data["budget"]
        activity.append(f"The timing pilot selected {b['updates']} updates per block at {b['seconds_per_update']:.1f} seconds per pilot update. A block at that rate would take {b['updates']*b['seconds_per_update']/3600:.2f} hours.")
        for r in data["runs"]:
            if r["name"]!="base" and r["updates"] is None and (RESULTS/r["name"]/"recipe.json").exists():
                activity.append(f"{r['name']} has scored {r['groups']} complete rollout groups against its target of {b['updates']}. The live dashboard reads incoming observations between releases.")
    atomic(REPORTS/"progress.md",f"# Progress · {date}\n\n{trained} of {data['planned']} registered training blocks have completed. {complete} have completed final evaluation. {status}\n\n"+"\n\n".join(activity)+"\n\nThe first single-seed solver has a 14-hour target. The matrix has a one-week training target. Monitoring cadence and milestone order are in the [plan](plan.md). The [experiment index](experiments/experiments.md) contains available development observations.\n")
    paper(data,date)
    return data
