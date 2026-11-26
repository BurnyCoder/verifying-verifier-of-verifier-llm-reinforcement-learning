"""Reproduce the learnability review on synthetic answers with real partition assignments."""

import pytest

from study.curriculum import curriculum_problems
from study.design import PILOTS
from study.learnability_analysis import learning_result
from study.records import render
from study.storage import append, read_json, write_json


def test_review_checks_actual_training_order_splits_and_every_validation_grade(tmp_path):
    from study.learning_review import check_release

    root = tmp_path/"learnability"
    assert check_release(tmp_path) is None
    config = {"family":"two-add", "style":"demonstrated"}
    write_json(root/"screen.json",{"selected":config})
    for phase,count in (("screen",16),("confirm",48)):
        for p in curriculum_problems("two-add",phase,count):
            append(root/phase/"two-add-demonstrated.jsonl",{"key":p.key})
    for name in PILOTS:
        write_json(tmp_path/name/"trained.json",{"updates":128,"run":{"seed":17,"family":"two-add","prompt_style":"demonstrated"}})
        for step,p in enumerate(curriculum_problems("two-add","train",128)):
            for sample in range(4):
                append(tmp_path/name/"rollouts.jsonl",dict(key=p.key,step=step,sample=sample,role="solver",trace="",prior=[]))
    samples = []
    for name in ("base",*PILOTS):
        labels = {}
        for p in curriculum_problems("two-add","validation",256):
            values=list(p.values)
            if name!=PILOTS[0]:
                values[0]+=1
            labels[p.key]=int(name==PILOTS[0])
            append(root/"evaluations"/(name+".jsonl"),dict(key=p.key,expression=p.expression,expected_values=p.values,
                   trace=render(values),correct=labels[p.key],parsed=True))
        write_json(root/"evaluations"/(name+".json"),dict(n=256,correct=sum(labels.values()),parsed=256))
        samples.append(labels)
    write_json(root/"learning.json",learning_result(*samples))
    verified=check_release(tmp_path)
    assert verified["scored"]==768 and verified["validation"]==256 and verified["training"]==128
    assert verified["overlap"]==0 and len(verified["exposure_hash"])==64
    learning = read_json(root/"learning.json")
    learning["over_base"]["fixed"] -= 1
    write_json(root/"learning.json",learning)
    with pytest.raises(ValueError,match="paired result"):
        check_release(tmp_path)
