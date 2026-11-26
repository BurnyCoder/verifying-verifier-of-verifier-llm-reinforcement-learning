"""Public role instructions. Numeric answer keys are never interpolated into a prompt."""

from functools import lru_cache

from .domain import Problem
from .records import expected, render

SOLVER = """Calculate each numbered step in order. s1, s2, etc. refer to earlier values.
Reply with just the comma-separated integer values, one per step, in order.
Example: s1 = 2 + 3 and s2 = s1 * 4 gives 5,20."""

FIRST = """You check every step in a submitted arithmetic trace. An incorrect intermediate value makes the trace invalid even if the last answer is right.
Reply with exactly three comma-separated integers: valid,step,value.
Correct trace: 1,0,final_value. Wrong trace: 0,first_wrong_step,correct_value_at_that_step. Missing or malformed trace: 0,-1,0.
Example: if s1 = 2+3 and s2 = s1*4, the submission 6,20 requires 0,1,5. The submission 5,20 requires 1,0,20."""

UPPER = """Audit the immediately preceding report, including each numerical claim. Return exactly six comma-separated integers:
sound,field,replacement,valid,step,value.
The last three grade the original solution: valid trace uses 1,0,final_value; an error uses 0,first_wrong_step,correct_value; malformed trace uses 0,-1,0.
The first three grade the previous judge. If its fields are all correct use 1,0,the_supported_value. Otherwise use 0,first_wrong_field_number,correct_replacement. A malformed preceding report uses 0,-1,0. Fields and steps start at one.
Judge 1 has three fields: valid,step,value. Judges 2 and 3 have the six fields above. A correct rejection of the solution is a sound report.
Example: the true solution report is 0,1,5. If Judge 1 said 0,1,6 then Judge 2 should say 0,3,5,0,1,5. A sound Judge 2 is endorsed by Judge 3 as 1,0,5,0,1,5."""


def messages(role, problem, trace="", history=(), style="registered"):
    if style=="demonstrated":
        return [*demonstrations(role),{"role":"user","content":exercise(role,problem,trace,history)}]
    if style!="registered":
        raise ValueError(f"Unknown prompt style {style}")
    content = "Problem\n" + problem.question
    if role == "solver":
        instruction = SOLVER
    else:
        instruction = FIRST if role == "j1" else UPPER
        content += "\nSubmitted solution\n" + trace
        for index, report in enumerate(history, 1):
            content += f"\nJudge {index} report\n{report}"
        content += f"\nReturn Judge {role[1:]} report."
    return [{"role": "system", "content": instruction}, {"role": "user", "content": content}]


def exercise(role, problem, trace="", history=()):
    content=problem.question
    if role=="solver":
        return content+"\nGive the numeric values in order."
    content+="\nSolver response: "+trace
    for level,claim in enumerate(history,1):
        content+=f"\nJudge {level}: {claim}"
    return content+f"\nYour Judge {role[1:]} record:"


@lru_cache(maxsize=4)
def demonstrations(role):
    """Only these public worked problems supply demonstration labels, never the active problem."""
    simple=Problem.from_expression("2+3")
    seven=Problem.from_expression("(4+3)*2")
    five=Problem.from_expression("(2+3)*4")
    turns=[]
    if role=="solver":
        system="Calculate every line. Answer with integers only, separated by commas. Use one integer for each line."
        examples=[(p,"",[]) for p in (simple,seven,five)]
    elif role=="j1":
        system=("Check the numeric trace. Write three integers only. For a correct trace give 1,0 and its final value. "
                "For a wrong trace give 0, the first wrong step number, and the correct value there. For bad format give 0,-1,0.")
        examples=[(five,"5,20",[]),(seven,"8,14",[]),(simple,"5",[]),(five,"s1,s2",[])]
    elif role in ("j2","j3"):
        system=("Write exactly six comma-separated integers. The FIRST triple checks the preceding judge: "
                "1,0,last_corrected_value if every field is right; otherwise 0,first_wrong_field_number,correct_replacement. "
                "For a malformed preceding judge the first triple is 0,-1,0. Fields count from one. "
                "The LAST triple checks the solver: 1,0,final_value for a correct trace, 0,first_wrong_step,correct_value for a wrong trace, "
                "or 0,-1,0 for a malformed trace. Judge 1 has three fields. Higher judges have six.")
        if role=="j2":
            examples=[(five,"5,20",["1,0,20"]),(seven,"8,14",["0,1,6"]),
                      (seven,"8,14",["0,1,7"]),(five,"5,20",["0,1,5"])]
        else:
            examples=[(five,"5,20",["1,0,20","1,0,20,1,0,20"]),
                      (seven,"8,14",["0,1,7","1,0,6,0,1,7"]),
                      (seven,"8,14",["0,1,7","1,0,7,0,1,7"]),
                      (five,"5,20",["1,0,20","1,0,19,1,0,20"])]
    else:
        raise ValueError(f"Unknown role {role}")
    turns.append({"role":"system","content":system})
    for p,t,h in examples:
        answer=p.values if role=="solver" else expected(p,t,h)
        turns.extend(({"role":"user","content":exercise(role,p,t,h)},{"role":"assistant","content":render(answer)}))
    return tuple(turns)
