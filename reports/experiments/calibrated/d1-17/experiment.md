# calibrated/d1-17

The solver adapter starts from a fresh LoRA initialization with seed 17. Its reward rule is d1. Frozen reviewer calls in order use the base model. The shared architecture, optimizer and sample definition are in the [registered protocol](../../../preregistration.md).

| Run | Updated role | Updates | Development exact | Development n | Held-out exact | Held-out n |
|---|---|---:|---:|---:|---:|---:|
| d1-17 | solver | 256 | 65.6% | 32 | — | 0 |

### Replaying the same solver outputs

| Split | Rule | Verdict agreement | Exact evidence / traces | False accepts / invalid | False rejects / valid | Malformed / reports |
| --- | --- | --- | --- | --- | --- | --- |
| Development | D1 | 62.5% | 17/32 | 11/11 | 1/21 | 0/32 |
| Development | D2 | 56.2% | 11/32 | 6/11 | 8/21 | 0/32 |
| Development | D3 | 56.2% | 10/32 | 6/11 | 8/21 | 0/32 |
| Development | Flat | 71.9% | — | 9/11 | 0/21 | 0/96 |

The flat panel contributes three ballots per trace. A zero denominator means the relevant class was absent.

| Split | Natural traces | J3 fixes | J3 harms | D3 − D2 verdict accuracy (pp) |
| --- | --- | --- | --- | --- |
| Development | 32 | 0 | 0 | +0.00 |

### Paired evidence interventions

| Split | Problem pairs | Whole pair exact | Masked whole pair exact |
| --- | --- | --- | --- |
| dev | 8 | 0.0% | 0.0% |

| Condition | Twin reports | Six fields parsed | Correct solution bit | Correct audit bit | Fault located and repaired / faulty reviews |
| --- | --- | --- | --- | --- | --- |
| visible | 16 | 15 | 14 | 8 | 0/8 |
| masked | 16 | 10 | 10 | 5 | 0/8 |

These evidence measurements use the identical frozen reviewer from base. They are shared observations.

### Training generation cost

| Role | Calls | Input tokens | Output tokens | CUDA event seconds |
| --- | --- | --- | --- | --- |
| solver | 1024 | 168240 | 6020 | 305.49 |
| j1 | 1024 | 289892 | 6992 | 263.53 |
| development_solver | 64 | 10528 | 353 | 12.39 |

[Machine observations](../../../../results/calibrated/d1-17)
