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
