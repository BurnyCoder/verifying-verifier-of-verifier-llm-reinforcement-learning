# Experiment index

All learned models use grouped reinforcement learning with one active LoRA adapter on the shared, quantized Qwen2.5-1.5B-Instruct backbone. The solver predicts values in signed-integer expression trees. Judges predict exact evidence records about earlier outputs. A parsed output supplies the required number of integers. An exact output also gets every field right.

| Run | Role | Reward | Seed | Problem source | Dev. parsed | Dev. exact | Held-out exact |
| --- | --- | --- | --- | --- | --- | --- | --- |
| base | solver | untrained | 17 | arithmetic | 18.8% | 0.0% | — |

[Update counts and sample sizes](../summary.md) · [Objectives and curricula](../planned-runs.md) · [Analysis protocol](../preregistration.md)

- [base](base/experiment.md)
