# Can this model learn the benchmark?

The frozen-model screen and the checkpoint comparison answer different questions. The screen measures attainable difficulty. The training probe measures change on a fresh validation sample. [Registered selection and decision rules](learnability-preregistration.md).

## Frozen-model screen

| Family | Prompt | Problems | Parsed samples | Sample exact | Greedy exact | Mixed groups |
| --- | --- | --- | --- | --- | --- | --- |
| one | registered | 16 | 1.6% | 0.0% | 0.0% | 0 |
| one | demonstrated | 16 | 81.2% | 81.2% | 93.8% | 4 |
| two-add | registered | 16 | 0.0% | 0.0% | 0.0% | 0 |
| two-add | demonstrated | 16 | 100.0% | 53.1% | 56.2% | 2 |
| two-mixed | registered | 16 | 0.0% | 0.0% | 0.0% | 0 |
| two-mixed | demonstrated | 16 | 100.0% | 56.2% | 75.0% | 5 |
| registered | registered | 16 | 35.9% | 0.0% | 0.0% | 0 |
| registered | demonstrated | 16 | 98.4% | 12.5% | 12.5% | 3 |

The registered rule selected two-add with demonstrated prompts.

Independent confirmation passed. On 48 problems, 99.0% of sampled outputs parsed, 54.2% were exact, and 16 groups contained both correct and incorrect answers.

## Frozen judges on balanced correct and incorrect traces

| Judge | Valid | Invalid | Sensitivity | Specificity | Balanced accuracy | Whole record exact | Malformed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 16 | 16 | 81.2% | 12.5% | 46.9% | 40.6% | 0 |
| 2 | 16 | 16 | 68.8% | 12.5% | 40.6% | 34.4% | 0 |
| 3 | 16 | 16 | 62.5% | 18.8% | 40.6% | 31.2% | 2 |

Judge 3 solved 0.0% of 16 complete evidence pairs with the review visible and 0.0% with evidence masked.

## Fresh learning-validation problems

| Checkpoint | Problems | Parsed | Entire trace correct | Exact accuracy |
| --- | --- | --- | --- | --- |
| base | 256 | 256 | 153 | 59.8% |
| learn-oracle-17 | 256 | 255 | 246 | 96.1% |

![Greedy complete-trace accuracy and available paired contrasts](../docs/assets/learnability.png)
