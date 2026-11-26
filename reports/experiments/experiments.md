# Experiment index

All learned models use grouped reinforcement learning with one active LoRA adapter on the shared, quantized Qwen2.5-1.5B-Instruct backbone. The solver predicts values in signed-integer expression trees. Judges predict exact evidence records about earlier outputs. A parsed output supplies the required number of integers. An exact output also gets every field right.

| Run | Role | Reward | Seed | Problem source | Dev. parsed | Dev. exact | Held-out exact |
| --- | --- | --- | --- | --- | --- | --- | --- |
| base | solver | untrained | 17 | arithmetic | 100.0% | 62.5% | — |
| d3-17 | solver | d3 | 17 | arithmetic | 96.9% | 9.4% | — |
| d2-17 | solver | d2 | 17 | arithmetic | 100.0% | 78.1% | — |
| learn-oracle-17 | solver | oracle | 17 | arithmetic | — | — | — |
| learn-shuffle-17 | solver | oracle-shuffle | 17 | arithmetic | — | — | — |

[Update counts and sample sizes](../summary.md) · [Objectives and curricula](../planned-runs.md) · [Analysis protocol](../preregistration.md)

- [base](calibrated/base/experiment.md)
- [d3-17](calibrated/d3-17/experiment.md)
- [d2-17](calibrated/d2-17/experiment.md)
- [learn-oracle-17](learn-oracle-17/experiment.md)
- [learn-shuffle-17](learn-shuffle-17/experiment.md)
- [Original base](base/experiment.md)
- [Original d3-17](d3-17/experiment.md)
