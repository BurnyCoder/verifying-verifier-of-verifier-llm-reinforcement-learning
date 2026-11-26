"""Summarize calibration cells and paired validation independently of the original benchmark."""

from html import escape

from .design import PILOTS
from .storage import read_json
from .tables import markdown, points, rate


def collect_learnability(results):
    root=results/"learnability"
    return dict(screen=read_json(root/"screen.json"),confirmation=read_json(root/"confirm.json"),
                audit=read_json(root/"audit.json"),learning=read_json(root/"learning.json"),
                evaluations={name:read_json(root/"evaluations"/(name+".json")) for name in ("base",*PILOTS)})


def learning_figure(data, path):
    """Plot observed accuracy and, once measured, paired improvements on the same problems."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    labels = {"base":"Starting solver",PILOTS[0]:"Exact reward",PILOTS[1]:"Shuffled reward"}
    colors = {"base":"#52656b",PILOTS[0]:"#167666",PILOTS[1]:"#a7562b"}
    measured = [(name,e) for name,e in data["evaluations"].items() if e]
    if not measured:
        path.unlink(missing_ok=True)
        return
    result = data["learning"]
    cols = 2 if result else 1
    fig, grid = plt.subplots(1,cols,figsize=(10.8 if result else 6.8,3.2),squeeze=False,layout="constrained")
    ax = grid[0,0]
    for i,(name,e) in enumerate(measured):
        score=100*e["correct"]/e["n"]
        ax.barh(i,score,color=colors[name],height=.52)
        inside=score >= 28
        ax.text(score-2 if inside else score+2,i,f"{e['correct']}/{e['n']}",
                ha="right" if inside else "left",va="center",color="white" if inside else "#1b3439")
    ax.set(yticks=range(len(measured)),yticklabels=[labels[name] for name,_ in measured],xlim=(0,100),
           xlabel="Entire trace correct (%)",title="Fresh validation problems")
    ax.invert_yaxis()
    if result:
        ax=grid[0,1]
        for i,key in enumerate(("over_base","over_shuffled")):
            statistic=result[key]
            value=100*statistic["delta"]
            low,high=[100*x for x in statistic["interval"]]
            ax.hlines(i,low,high,color=colors[PILOTS[0]],linewidth=2)
            ax.plot(value,i,"o",color=colors[PILOTS[0]])
            ax.text(value,i+.16,f"{value:+.1f}  [{low:+.1f}, {high:+.1f}]",ha="center",va="top",fontsize=9)
        ax.axvline(0,color="#657477",linestyle="--",linewidth=1)
        ax.set(yticks=[0,1],yticklabels=["vs starting solver","vs shuffled reward"],ylim=(1.5,-.35),
               xlabel="Percentage-point difference",title="Exact reward · paired 95% intervals")
        ax.margins(x=.22)
    for ax in grid.flat:
        ax.spines[["top","right"]].set_visible(False)
    path.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(path,dpi=150,bbox_inches="tight")
    plt.close(fig)


def learnability_text(data):
    out=["# Can this model learn the benchmark?",
         "The frozen-model screen and the checkpoint comparison answer different questions. "
         "The screen measures attainable difficulty. The training probe measures change on a fresh validation sample. "
         "[Registered selection and decision rules](learnability-preregistration.md)."]
    screen=data["screen"]
    if not screen:
        return "\n\n".join([*out,"The frozen-model screen is pending."])+"\n"
    out.extend(["## Frozen-model screen",
                markdown(["Family","Prompt","Problems","Parsed samples","Sample exact","Greedy exact","Mixed groups"],
                         [[c["family"],c["style"],c["problems"],rate(c["parsed"]),rate(c["sampled_exact"]),
                           rate(c["greedy_exact"]),c["mixed_groups"]] for c in screen["cells"]])])
    chosen=screen["selected"]
    out.append(f"The registered rule selected {chosen['family']} with {chosen['style']} prompts." if chosen else
               "No configuration qualified under the registered rule.")
    if chosen and chosen["family"]=="one":
        out.append("With one operation, final-answer accuracy and complete-trace accuracy coincide. The harder signed transfer cohort tests intermediate-step correctness.")
    if data["confirmation"]:
        c=data["confirmation"]["cell"]
        passed="passed" if data["confirmation"]["confirmed"] else "failed"
        out.append(f"Independent confirmation {passed}. On {c['problems']} problems, {rate(c['parsed'])} of sampled outputs parsed, "
                   f"{rate(c['sampled_exact'])} were exact, and {c['mixed_groups']} groups contained both correct and incorrect answers.")
    if data["audit"]:
        a=data["audit"]
        out.extend(["## Frozen judges on balanced correct and incorrect traces",
                    markdown(["Judge","Valid","Invalid","Sensitivity","Specificity","Balanced accuracy","Whole record exact","Malformed"],
                             [[j["level"],j["valid"],j["invalid"],rate(j["sensitivity"]),rate(j["specificity"]),
                               rate(j["balanced_accuracy"]),rate(j["evidence"]),j["malformed"]] for j in a["judges"]]),
                    f"Judge 3 solved {rate(a['visible'])} of {a['pairs']} complete evidence pairs with the review visible and {rate(a['masked'])} with evidence masked."])
    measured=[(name,e) for name,e in data["evaluations"].items() if e]
    if measured:
        out.extend(["## Fresh learning-validation problems",markdown(["Checkpoint","Problems","Parsed","Entire trace correct","Exact accuracy"],
                   [[name,e["n"],e["parsed"],e["correct"],rate(e["correct"]/e["n"])] for name,e in measured])])
        out.append("![Greedy complete-trace accuracy and available paired contrasts](../docs/assets/learnability.png)")
    if data["learning"]:
        result=data["learning"]
        out.append("The registered learning criterion was "+("met." if result["demonstrated"] else "unmet."))
        out.append("The paired comparison also supports a reward-specific improvement." if result["reward_specific"] else
                   "The evidence did not meet the registered criterion for a reward-specific improvement.")
        out.append(markdown(["Exact-trained minus","Gain (pp)","95% lower (pp)","95% upper (pp)","Fixed","Harmed"],
                   [[label,points(r["delta"]),*(points(x) for x in r["interval"]),r["fixed"],r["harmed"]]
                    for label,r in (("Frozen base",result["over_base"]),("Shuffled control",result["over_shuffled"]))]))
        for comparator, breakdown in result.get("by_parse", {}).items():
            out.extend([f"### Formatting and arithmetic changes against {comparator}",
                        markdown(["Parse status","Problems","Gained complete correctness","Lost complete correctness"],
                                 [[g["stratum"],g["n"],g["gains"],g["losses"]] for g in breakdown["groups"]])])
            for ex in breakdown["examples"]:
                reference = ",".join(map(str,ex["expected"]))
                text = (f"Problem   {ex['expression']}\nExpected  {reference}\nComparator\n{ex['comparator']}"
                        f"\nExact-trained\n{ex['trained']}")
                out.append(f"{ex['stratum']} · {ex['change']}\n\n<pre>{escape(text)}</pre>")
        out.append("[Independent arithmetic replay, paired estimates and realized split checks](reviews/learning-control.md).")
    return "\n\n".join(out)+"\n"
