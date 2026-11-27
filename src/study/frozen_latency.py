"""Clock-only eligibility check for the 27B deployment after a slowdown survives a fresh load."""


def slow_segment(calls, fits):
    """Use recorded call times and identical-file loads. The policy never reads a prediction or label."""
    loads = [r for r in fits if r['fit']]
    measured = [r for r in calls if not r['id'].startswith('timing/')]
    if not loads or not measured or measured[-1]['time'] <= loads[-1]['time']:
        return None
    def streak(group):
        last = group[-3:]
        return last if len(last)==3 and all(r['elapsed_seconds']>30 for r in last) else []
    tail = streak(measured)
    if not tail:
        return None
    previous = streak([r for r in measured if r['time']<loads[-1]['time']])
    reloaded = len(loads)>=2 and loads[-1]['file']==loads[-2]['file'] and bool(previous)
    evidence = {r['id']:{'id':r['id'],'time':r['time'],'seconds':r['elapsed_seconds']} for r in (*previous,*tail)}
    return dict(reloaded=reloaded, file=loads[-1]['file'], evidence=list(evidence.values()),
                calls=len(measured), latest_load=loads[-1]['time'])


class ReloadSlowJudge(RuntimeError):
    """Release the native process and replay the incomplete case on the same weights."""
