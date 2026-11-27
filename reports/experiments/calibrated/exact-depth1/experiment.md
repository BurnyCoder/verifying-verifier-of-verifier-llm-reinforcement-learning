# calibrated/exact-depth1

The solver adapter starts from a fresh LoRA initialization with seed 17. Its reward rule is d1. Frozen reviewer calls in order use exact-j1. The shared architecture, optimizer and sample definition are in the [registered protocol](../../../preregistration.md).

| Run | Updated role | Updates | Development exact | Development n | Held-out exact | Held-out n |
|---|---|---:|---:|---:|---:|---:|
| exact-depth1 | solver | 256 | 62.5% | 32 | — | 0 |

### Replaying the same solver outputs

| Split | Rule | Verdict agreement | Exact evidence / traces | False accepts / invalid | False rejects / valid | Malformed / reports |
| --- | --- | --- | --- | --- | --- | --- |
| Development | D1 | 62.5% | 20/32 | 12/12 | 0/20 | 0/32 |
| Development | D2 | 62.5% | 20/32 | 12/12 | 0/20 | 0/32 |
| Development | D3 | 62.5% | 20/32 | 12/12 | 0/20 | 0/32 |
| Development | Flat | 62.5% | — | 12/12 | 0/20 | 0/96 |

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
| visible | 16 | 15 | 15 | 8 | 0/8 |
| masked | 16 | 0 | 0 | 0 | 0/8 |

These evidence measurements use the identical frozen reviewer from exact-j3. They are shared observations.

### Training generation cost

| Role | Calls | Input tokens | Output tokens | CUDA event seconds |
| --- | --- | --- | --- | --- |
| solver | 1024 | 168240 | 6020 | 214.66 |
| j1 | 1024 | 289895 | 7001 | 238.80 |
| development_solver | 64 | 10528 | 352 | 7.59 |

[Machine observations](../../../../results/calibrated/exact-depth1)
