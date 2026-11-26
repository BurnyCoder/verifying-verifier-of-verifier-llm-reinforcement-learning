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
    return "\n\n".join(out)+"\n"
