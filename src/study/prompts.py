"""Public role instructions. Numeric answer keys are never interpolated into a prompt."""

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


def messages(role, problem, trace="", history=()):
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
