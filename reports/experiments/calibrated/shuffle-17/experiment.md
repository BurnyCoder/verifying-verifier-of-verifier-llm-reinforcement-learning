# calibrated/shuffle-17

The solver adapter starts from a fresh LoRA initialization with seed 17. Its reward rule is shuffle. Frozen reviewer calls in order use the base model, the base model, the base model. The shared architecture, optimizer and sample definition are in the [registered protocol](../../../preregistration.md).

| Run | Updated role | Updates | Development exact | Development n | Held-out exact | Held-out n |
|---|---|---:|---:|---:|---:|---:|
| shuffle-17 | solver | 256 | 15.6% | 32 | — | 0 |

### Replaying the same solver outputs

| Split | Rule | Verdict agreement | Exact evidence / traces | False accepts / invalid | False rejects / valid | Malformed / reports |
| --- | --- | --- | --- | --- | --- | --- |
| Development | D1 | 15.6% | 4/32 | 27/27 | 0/5 | 0/32 |
| Development | D2 | 56.2% | 4/32 | 14/27 | 0/5 | 0/32 |
| Development | D3 | 56.2% | 4/32 | 14/27 | 0/5 | 0/32 |
| Development | Flat | 21.9% | — | 25/27 | 0/5 | 0/96 |

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
| solver | 1024 | 168240 | 5941 | 296.37 |
| j1 | 1024 | 289832 | 6995 | 259.62 |
| j2 | 1024 | 454523 | 13985 | 502.64 |
| j3 | 1024 | 549404 | 14017 | 536.31 |
| development_solver | 64 | 10528 | 344 | 11.53 |

[Machine observations](../../../../results/calibrated/shuffle-17)
