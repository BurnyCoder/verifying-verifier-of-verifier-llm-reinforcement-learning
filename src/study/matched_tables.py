"""Compare judge depths only when the arithmetic questions or saved solver answers are identical."""

from .design import ROUTES
from .paired_examples import explain_report, literal
from .storage import rows
from .tables import markdown


HEADERS = ["Training condition","One judge · J1","Two judges · J2 checks J1","Three judges · J3 checks J2"]
PENDING = "Pending"


def solver_arms(route):
    if route=="frozen":
        return ("d1-17","d2-17","d3-17")
    return (route+"-depth1",route+"-depth2",route+"-prefix3")


def cell(correct,n):
    return f"{correct}/{n} ({100*correct/n:.1f}%)"


def read_cohort(path,reference,judge=False):
    """The report fails on duplicate, missing, reordered or mismatched comparison units."""
    data = list(rows(path))
    fields = ("key","expression","trace","correct") if judge else ("key","expression")
    if (len(data)!=len(reference) or len({r["key"] for r in data})!=len(data) or
            any(any(a[k]!=b[k] for k in fields) for a,b in zip(reference,data,strict=True))):
        raise ValueError(f"Unmatched {'solver responses' if judge else 'questions'} in {path}")
    return data


def accuracy_grid(root,profile):
    if not profile:
        return []
    grids = []
    for phase in ("development","final"):
        if not (root/"base"/(phase+".json")).is_file():
            continue
        is_dev = phase=="development"
        solver_file = "replay.jsonl" if is_dev else "test.jsonl"
        judge_file = "replay.jsonl" if is_dev else "judge-test.jsonl"
        base = list(rows(root/"base"/solver_file))
        shared = base if is_dev else list(rows(root/"base"/judge_file))
        if (len(base),len(shared)) != ((32,32) if is_dev else (2048,128)):
            raise ValueError(f"Incomplete base cohort for the {phase} tables")
        solver_table,judge_table = [],[]
        valid = sum(r["correct"] for r in shared)
        changed = [r for r in shared if r["verdicts"][1] != r["verdicts"][2]]
        fixes = sum(r["verdicts"][2] == r["correct"] for r in changed)
        notes = [f"On the original frozen judges’ row, Judge 3 fixed Judge 2’s verdict on {fixes}/{len(shared)} "
                 f"answers and introduced a grading error on {len(changed)-fixes}/{len(shared)}.",
                 f"Always accepting scores {cell(valid,len(shared))} on these same responses."]
        route_labels = {"frozen":"Only solver trained · original judges","exact":"Exact-trained judges, then solver",
                        "top":"Top-down-trained judges, then solver"}
        for route,label in route_labels.items():
            values = []
            for name in solver_arms(route):
                if (root/name/(phase+".json")).is_file():
                    records = read_cohort(root/name/solver_file,base)
                    values.append(cell(sum(r["correct"] for r in records),len(records)))
                else:
                    values.append(PENDING)
            solver_table.append([label,*values])
        def score(records,level):
            return cell(sum(row["verdicts"][level]==row["correct"] for row in records),len(records))
        judge_table.append(["Original frozen judges",*[score(shared,i) for i in range(3)]])
        for route,label in (("exact","Exact labels"),("top","Top-down supervision")):
            isolated = []
            for i,name in enumerate(ROUTES[route]):
                block = root/name
                if not (block/(phase+".json")).is_file():
                    isolated.append(PENDING)
                    continue
                records = read_cohort(block/judge_file,shared,judge=True)
                if any(a["reports"][:i]!=b["reports"][:i] for a,b in zip(records,shared,strict=True)):
                    raise ValueError(f"Preceding reports changed for the isolated {name} comparison")
                isolated.append(score(records,i))
            judge_table.append([label+" · only final judge trained",*isolated])
            fitted = [isolated[0],PENDING,PENDING]
            replay = root/"matched-depth"/f"{route}-{phase}"
            if replay.with_suffix(".json").is_file():
                records = read_cohort(replay.with_suffix(".jsonl"),shared,judge=True)
                fitted = [score(records,i) for i in range(3)]
                first = read_cohort(root/ROUTES[route][0]/judge_file,shared,judge=True)
                if any(a["reports"][0]!=b["reports"][0] for a,b in zip(first,records,strict=True)):
                    raise ValueError(f"Identical trained Judge 1 reports differ across {route} conditions")
                approved = [sum(r["verdicts"][i] for r in records) for i in range(3)]
                inaccurate = [sum(r["verdicts"][i] and not r["correct"] for r in records) for i in range(3)]
                stack_label = "stack trained on exact labels" if route=="exact" else "stack trained top-down"
                if all(n==len(records) for n in approved):
                    notes.append(f"The {stack_label} approved all {len(records)} answers at every depth, "
                                 f"including all {len(records)-valid} incorrect solutions.")
                else:
                    total_text = ", ".join(map(str,approved))
                    wrong_text = ", ".join(map(str,inaccurate))
                    faults = len(records)-valid
                    errors = (f"It accepted all {faults} incorrect solutions at every depth."
                              if faults and all(n==faults for n in inaccurate) else
                              f"False approvals numbered {wrong_text}, with {faults} incorrect solutions per depth.")
                    notes.append(f"The {stack_label} approved {total_text} answers at depths one, two and three, "
                                 f"respectively. {errors}")
            judge_table.append([label+" · all participating judges trained",*fitted])
        frozen_changes = [{k: r[k] for k in ("key","expression","trace","expected_values","correct","reports","verdicts")}
                          for r in changed]
        grids.append(dict(phase=phase,solver=solver_table,judge=judge_table,solver_n=len(base),judge_n=len(shared),
                          frozen_changes=frozen_changes,
                          frozen_solver=cell(sum(r["correct"] for r in base),len(base)),judge_note=" ".join(notes)))
    return grids


def grid_markdown(grids):
    if not grids:
        return ""
    sections = ["## Matched accuracy by judge depth",
                "Each column adds one review of the preceding judge. Judge 1 checks the solver, Judge 2 checks Judge 1, "
                "and Judge 3 checks Judge 2. Across a solver-training row only the depth of its reward changes. "
                "All solver comparisons here use seed 17."]
    for grid in reversed(grids):
        split = "Development" if grid["phase"]=="development" else "Held-out"
        sections += [f"### {split} solver accuracy",f"Every solver answers the same {grid['solver_n']:,} questions. "
            "A solution is correct when every intermediate value is correct. Fitted judges stay frozen during solver updates.",
            markdown(HEADERS,grid["solver"]),f"### {split} judge verdict accuracy",
            f"Every judge grades the same {grid['judge_n']} saved responses from the starting solver. A verdict is correct "
            f"when it agrees with the arithmetic checker. In all judge-only conditions the solver itself stays at {grid['frozen_solver']} "
            f"on the {grid['solver_n']:,} solver-evaluation questions.",markdown(HEADERS,grid["judge"]),grid["judge_note"]]
        if grid["frozen_changes"]:
            examples = []
            for record in grid["frozen_changes"]:
                j2, j3 = [explain_report(record["reports"][i], i+1, record["verdicts"][i]) for i in (1, 2)]
                outcome = "Fixed a grading error" if record["verdicts"][2] == record["correct"] else "Introduced a grading error"
                examples.append([literal(record["expression"]), literal(record["trace"]),
                                 literal(",".join(map(str,record["expected_values"]))),j2,j3,outcome])
            table = markdown(["Problem","Starting solver wrote","Correct steps","Judge 2","Judge 3","Effect"],examples)
            sections.append("<details><summary>Every verdict Judge 3 changed on the starting solver’s saved answers</summary>\n\n"
                            +table+"\n\n</details>")
    sections.append("“Only final judge trained” fits the judge used for that column’s terminal decision and uses original "
                    "judges for preceding calls. “All participating judges trained” uses fitted adapters at every depth. "
                    "Top-down training uses the shared exact-trained Judge 3. Pending cells have no completed matched measurement. "
                    "[Matched comparison protocol](reports/matched-depth-protocol.md)")
    return "\n\n".join(sections)+"\n\n"
