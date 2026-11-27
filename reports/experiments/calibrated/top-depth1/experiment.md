# calibrated/top-depth1

The solver adapter starts from a fresh LoRA initialization with seed 17. Its reward rule is d1. Frozen reviewer calls in order use top-j1. The shared architecture, optimizer and sample definition are in the [registered protocol](../../../preregistration.md).

| Run | Updated role | Updates | Development exact | Development n | Held-out exact | Held-out n |
|---|---|---:|---:|---:|---:|---:|
| top-depth1 | solver | 256 | 78.1% | 32 | — | 0 |

### Replaying the same solver outputs

| Split | Rule | Verdict agreement | Exact evidence / traces | False accepts / invalid | False rejects / valid | Malformed / reports |
| --- | --- | --- | --- | --- | --- | --- |
| Development | D1 | 78.1% | 19/32 | 7/7 | 0/25 | 0/32 |
| Development | D2 | 71.9% | 18/32 | 7/7 | 2/25 | 0/32 |
| Development | D3 | 71.9% | 18/32 | 7/7 | 2/25 | 0/32 |
| Development | Flat | 78.1% | — | 7/7 | 0/25 | 0/96 |

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
| solver | 1024 | 168240 | 5989 | 206.39 |
| j1 | 1024 | 289863 | 7002 | 235.14 |
| development_solver | 64 | 10528 | 353 | 7.55 |

[Machine observations](../../../../results/calibrated/top-depth1)
