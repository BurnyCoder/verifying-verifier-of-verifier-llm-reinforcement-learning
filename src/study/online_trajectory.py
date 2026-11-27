"""Reconstruct where the two solver trajectories first diverged and what the extra judge changed."""

from itertools import batched, tee

from .depth_review import different_group_credit, effective_bit
from .design import GITHUB
from .domain import Problem
from .learning_review import execute_steps
from .tables import markdown


def cross_run_differences(shallow, deep):
    """Find the first differing sampled texts and actual relative credits on matched prompt groups."""
    first_answer = first_credit = None
    same_answers = different_credits = 0
    first_difference = {}
    for update,(a,b) in enumerate(zip(batched(shallow,4),batched(deep,4),strict=True),1):
        answers = [[r["answer"] for r in group] for group in (a,b)]
        left, right = [[r["reward"] for r in group] for group in (a,b)]
        same_answers += answers[0]==answers[1]
        if first_answer is None and answers[0]!=answers[1]:
            first_answer = update
            first_difference = dict(expression=b[0]["expression"], answers=answers, rewards=[left,right])
        if different_group_credit(left,right):
            different_credits += 1
            if first_credit is None:
                first_credit = update
    return dict(first_answer_difference=first_answer, first_credit_difference=first_credit, first_difference=first_difference,
                same_answers=same_answers,different_credits=different_credits)


def trajectory_evidence(shallow, deep):
    """Compare actual trajectories and the alternative verdicts on the three-judge run's answers."""
    for_comparison, for_audit = tee(deep)
    observed = cross_run_differences(shallow, for_comparison)
    examples = {}
    for update,b in enumerate(batched(for_audit,4),1):
        right = [r["reward"] for r in b]
        # This counterfactual holds the entire deep-run solver group and the earlier reports fixed.
        lower = [effective_bit(r["reports"][1]) for r in b]
        if lower!=right:
            category = "relative" if different_group_credit(lower,right) else "constant"
            if category not in examples:
                p = Problem.from_expression(b[0]["expression"])
                examples[category] = dict(update=update, expression=p.expression, expected=list(execute_steps(p)),
                    group=[dict(answer=r["answer"],label=r["label"],reports=r["reports"]) for r in b],
                    two=lower,three=right)
    return dict(**observed,examples=examples)


def trajectory_note(evidence):
    """Report the time ordering without assigning a cause to unexplained numerical or sampling differences."""
    first = evidence["first_answer_difference"]
    credit = evidence["first_credit_difference"]
    if first is None:
        return "The two training runs sampled the same four literal answers at every update."
    note = f"The first difference in sampled solver answers occurred at update {first}."
    if credit is None or credit>=first:
        note += " All earlier groups gave the two solvers the same relative credit. An earlier change in judge credit therefore cannot explain this first divergence. The logs do not identify which computation produced the differing sample."
    else:
        note += f" The two runs had already assigned different relative credit at update {credit}."
    return note


def trajectory_text(evidence):
    """Show the earliest observed group in each category, selected in chronological order."""
    if not evidence:
        return ""
    intro = trajectory_note(evidence)
    first = evidence["first_difference"]
    if first:
        data = [[f"Judge {i}", *(f"`{a}`" for a in answers), str(bits)]
                for i,(answers,bits) in enumerate(zip(first["answers"],first["rewards"],strict=True),2)]
        intro += (f"\n\nBoth runs received `{first['expression']}` at that update.\n\n"+
                  markdown(["Solver trained with","Sample 1","Sample 2","Sample 3","Sample 4","Actual rewards"],data))
    result = ["### When did training first differ?",intro]
    for kind,ex in evidence["examples"].items():
        note = ("Both groups of four received uniform rewards, so every centered advantage was zero." if kind=="constant"
                else "Judge 3 changed how this group divided relative credit among its four answers.")
        data = [[f"`{row['answer']}`",row["label"],f"`{row['reports'][1]}`",a,f"`{row['reports'][2]}`",b]
                for row,a,b in zip(ex["group"],ex["two"],ex["three"],strict=True)]
        result.extend([f"At update {ex['update']}, `{ex['expression']}` required `{', '.join(map(str,ex['expected']))}`. {note}",
                       markdown(["Solver wrote","Exact","Judge 2 wrote","J2 reward","Judge 3 wrote","J3 reward"],data)])
    result.append("These descriptive examples use the first group in each observed category. Binary rewards are centered within each four-answer group. The fourth field in a parsed higher-order report supplies the solver verdict. "
                  f"[Reward implementation]({GITHUB}/blob/main/src/study/training.py) · [Raw groups]({GITHUB}/tree/main/results/new-judges) · [TRL GRPO](https://huggingface.co/docs/trl/grpo_trainer) · [PyTorch reproducibility](https://docs.pytorch.org/docs/stable/notes/randomness.html).")
    return "\n\n".join(result)+"\n\n"
