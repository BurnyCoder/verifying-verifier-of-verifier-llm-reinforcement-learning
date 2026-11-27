"""Reconstruct scores, input histories and evidence interventions from closed GPU journals."""

from .domain import Problem
from .frozen_cases import metrics
from .learning_review import execute_steps
from .prompts import messages
from .records import expected, mask_evidence, parse, render, solver_truth, sound, terminal
from .storage import rows


def confirmation_identities(screen_keys, expected_keys, control, winner):
    """Check every input pair, including the literal J1 report and both controlled J2 reviews."""
    if expected_keys & screen_keys:
        raise ValueError('Confirmation and screening problem IDs overlap')
    expected_cases = {f'{kind}/{key}' for key in expected_keys for kind in ('twins','balanced-valid','balanced-invalid')}
    if control.keys()!=expected_cases or winner.keys()!=expected_cases:
        raise ValueError('Confirmation cases differ from the preregistered problem IDs or conditions')
    for key in expected_cases:
        if any(control[key].get(f)!=winner[key].get(f) for f in ('kind','key','expression','trace','first','reviews')):
            raise ValueError(f'Candidate and control received different inputs on {key}')
    return len(expected_keys)


def confirmation_review(root, decision):
    """Rebuild the inclusion, selection, model identities, paired effects and gate from the release."""
    from .curriculum import curriculum_problems
    from .frozen_cases import paired_confirmation
    from .frozen_models import LOCAL_REPLICATES, MODELS
    from .storage import read_json
    family = read_json(root.parent/'calibrated/profile.json')['family']
    stream = curriculum_problems(family,'confirm',320)
    expected_screen, expected_confirm = ({p.key for p in stream[start:stop]} for start,stop in ((96,128),(256,320)))
    candidates, all_screen = {}, set()
    for key in [*(m.key for m in (*LOCAL_REPLICATES,*MODELS)), 'q38-27b-iq1s']:
        local = list(rows(root/key/'cases.jsonl'))
        all_screen.update(r['key'] for r in local)
        receipt = read_json(root/key/'result.json',{})
        if receipt.get('status')!='Complete':
            continue
        if {c['key'] for c in local if c['kind']=='twins'}!=expected_screen:
            raise ValueError(f'Unexpected arithmetic IDs for the {key} evidence screen')
        if key in {m.key for m in MODELS[1:]} or key=='q38-27b-iq1s':
            metrics=receipt['metrics']
            candidates[key]=(metrics['twins']['visible'], metrics['balanced']['depths'][2]['accuracy'], -receipt['cost']['elapsed_seconds'])
    chosen = max(candidates,key=candidates.get)
    if chosen!=decision['selected']:
        raise ValueError('Raw screen ranking disagrees with the confirmed selection')
    original = {key:score for key,score in candidates.items() if key!='q38-27b-iq1s'}
    if 'original_completed_selection' in decision and max(original,key=original.get)!=decision['original_completed_selection']:
        raise ValueError('Original completed candidate ranking disagrees with its release')
    def settings(key):
        return {k:v for k,v in read_json(root/key/'configuration.json').items() if k!='phase'}
    if settings(chosen)!=settings('confirm-winner') or settings(MODELS[0].key)!=settings('confirm-control'):
        raise ValueError('Screen and confirmation used different model files or inference settings')
    control, winner = ({r['id']:r for r in rows(root/key/'cases.jsonl')} for key in ('confirm-control','confirm-winner'))
    count = confirmation_identities(all_screen,expected_confirm,control,winner)
    estimates = paired_confirmation(winner,control)
    if estimates!=decision['estimates'] or all(e['delta']>0 for e in estimates.values())!=decision['online_gate']:
        raise ValueError('Released intervals or online gate disagree with the paired records')
    return dict(screen_ids=len(all_screen), fresh_ids=count, matched_cases=len(control), ranked_candidates=len(candidates))


def audit(folder, receipt):
    """Audit the scored output boundary without interpreting the server's prefilling as model text."""
    data = list(rows(folder/"cases.jsonl"))
    calls = {r["id"]:r for r in rows(folder/"calls.jsonl")}
    example = {}
    counter = 0
    identical_masked = 0
    error_positions = {"nonfinal":0,"final":0}

    def checked(call_id,level,p,trace,history):
        nonlocal counter
        c = calls[call_id]
        if (c["messages"]!=messages(f"j{level}",p,trace,history,"demonstrated") or
                not isinstance(c["generated_token_ids"],list) or len(c["generated_token_ids"])>48):
            raise ValueError(f"Unmatched prompt or token budget in {folder.name}/{call_id}")
        counter+=1
        return c
    for r in sorted(data,key=lambda x:(x["key"],x["kind"])):
        p = Problem.from_expression(r["expression"])
        if p.key!=r["key"] or tuple(execute_steps(p))!=p.values:
            raise ValueError("Independent arithmetic evaluator disagrees")
        if r["kind"]=="twins":
            masked = []
            for mode in ("visible","masked"):
                passed = True
                for i,review in enumerate(r["reviews"]):
                    actual = review if mode=="visible" else mask_evidence(review)
                    c = checked(f"{r['id']}/{mode}/{i}",3,p,r["trace"],[r["first"],actual])
                    truth = expected(p,r["trace"],[r["first"],review])
                    if c["text"]!=r[mode]["outputs"][i] or list(truth)!=r["labels"][i]:
                        raise ValueError("Logged judge output or exact reference changed")
                    passed &= sound(c["text"],truth)
                    if mode=="masked":
                        masked.append(c)
                if passed!=r[mode]["correct"]:
                    raise ValueError("Recorded whole-pair grade disagrees with raw generations")
            if masked[0]["rendered_prompt"]!=masked[1]["rendered_prompt"]:
                raise ValueError("The mask did not remove the distinguishing evidence")
            identical_masked += masked[0]["generated_token_ids"]==masked[1]["generated_token_ids"]
            outcome = "passed" if r["visible"]["correct"] else "failed"
            example.setdefault(outcome,dict(key=p.key,expression=p.expression,trace=r["trace"],first=r["first"],
                                       reviews=r["reviews"],outputs=r["visible"]["outputs"],expected=[render(v) for v in r["labels"]]))
        else:
            solution = solver_truth(p,r["trace"])
            verdict = solution[0]
            if r["kind"]=="balanced-invalid":
                error_positions["final" if solution[1]==len(p.values) else "nonfinal"]+=1
            history = []
            for level in (1,2,3):
                c = checked(f"{r['id']}/j{level}",level,p,r["trace"],history)
                truth = expected(p,r["trace"],history)
                bit = terminal(c["text"],level)
                grade = dict(verdict=bit,agreement=int(bit==verdict),full=int(sound(c["text"],truth)),
                             malformed=parse(c["text"],len(truth)) is None,expected=list(truth))
                if grade!=r["grades"][level-1] or c["text"]!=r["reports"][level-1] or verdict!=r["valid"]:
                    raise ValueError("Logged chain disagrees with executable rescore")
                history.append(c["text"])
    if metrics(data)!=receipt["metrics"] or counter!=receipt["cost"]["calls"] or len(calls)!=counter+4:
        raise ValueError("Published summary disagrees with complete raw observations")
    return dict(calls=counter,matched_masked_outputs=identical_masked,error_positions=error_positions,examples=example)
