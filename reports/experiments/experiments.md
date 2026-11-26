# Experiment index

All learned models use grouped reinforcement learning with one active LoRA adapter on the shared, quantized Qwen2.5-1.5B-Instruct backbone. The solver predicts values in signed-integer expression trees. Judges predict exact evidence records about earlier outputs. A parsed output supplies the required number of integers. An exact output also gets every field right.

| Run | Role | Reward | Seed | Problem source | Dev. parsed | Dev. exact | Held-out exact |
| --- | --- | --- | --- | --- | --- | --- | --- |
| base | solver | untrained | 17 | arithmetic | 100.0% | 62.5% | — |
| d3-17 | solver | d3 | 17 | arithmetic | 96.9% | 9.4% | — |
| d2-17 | solver | d2 | 17 | arithmetic | 100.0% | 78.1% | — |
| d1-17 | solver | d1 | 17 | arithmetic | 100.0% | 65.6% | — |
| flat-17 | solver | flat | 17 | arithmetic | 87.5% | 75.0% | — |
| oracle-17 | solver | oracle | 17 | arithmetic | 100.0% | 100.0% | — |
| hybrid-17 | solver | hybrid | 17 | arithmetic | 100.0% | 96.9% | — |
| shuffle-17 | solver | shuffle | 17 | arithmetic | 100.0% | 15.6% | — |
| exact-j1 | j1 | exact | 17 | base | 100.0% | 62.5% | — |
| exact-j2 | j2 | exact | 17 | base | 100.0% | 46.9% | — |
| exact-j3 | j3 | exact | 17 | base | 96.9% | 31.2% | — |
| top-j2 | j2 | teacher | 17 | base | 100.0% | 43.8% | — |
| top-j1 | j1 | teacher | 17 | base | 100.0% | 50.0% | — |
| exact-prefix1 | solver | d3 | 17 | arithmetic | 100.0% | 75.0% | — |
| exact-prefix2 | solver | d3 | 17 | arithmetic | — | — | — |
| learn-oracle-17 | solver | oracle | 17 | arithmetic | — | — | — |
| learn-shuffle-17 | solver | oracle-shuffle | 17 | arithmetic | — | — | — |

[Update counts and sample sizes](../summary.md) · [Objectives and curricula](../planned-runs.md) · [Analysis protocol](../preregistration.md)

- [base](calibrated/base/experiment.md)
- [d3-17](calibrated/d3-17/experiment.md)
- [d2-17](calibrated/d2-17/experiment.md)
- [d1-17](calibrated/d1-17/experiment.md)
- [flat-17](calibrated/flat-17/experiment.md)
- [oracle-17](calibrated/oracle-17/experiment.md)
- [hybrid-17](calibrated/hybrid-17/experiment.md)
- [shuffle-17](calibrated/shuffle-17/experiment.md)
- [exact-j1](calibrated/exact-j1/experiment.md)
- [exact-j2](calibrated/exact-j2/experiment.md)
- [exact-j3](calibrated/exact-j3/experiment.md)
- [top-j2](calibrated/top-j2/experiment.md)
- [top-j1](calibrated/top-j1/experiment.md)
- [exact-prefix1](calibrated/exact-prefix1/experiment.md)
- [exact-prefix2](calibrated/exact-prefix2/experiment.md)
- [learn-oracle-17](learn-oracle-17/experiment.md)
- [learn-shuffle-17](learn-shuffle-17/experiment.md)
- [Original base](base/experiment.md)
- [Original d3-17](d3-17/experiment.md)
