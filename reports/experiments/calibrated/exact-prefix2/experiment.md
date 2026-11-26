# calibrated/exact-prefix2

The solver adapter starts from a fresh LoRA initialization with seed 17. Its reward rule is d3. Frozen reviewer calls in order use exact-j1, exact-j2, the base model. The shared architecture, optimizer and sample definition are in the [registered protocol](../../../preregistration.md).

| Run | Updated role | Updates | Development exact | Development n | Held-out exact | Held-out n |
|---|---|---:|---:|---:|---:|---:|
| exact-prefix2 | solver | 256 | 12.5% | 32 | — | 0 |

### Replaying the same solver outputs

| Split | Rule | Verdict agreement | Exact evidence / traces | False accepts / invalid | False rejects / valid | Malformed / reports |
| --- | --- | --- | --- | --- | --- | --- |
| Development | D1 | 12.5% | 4/32 | 28/28 | 0/4 | 0/32 |
| Development | D2 | 12.5% | 4/32 | 28/28 | 0/4 | 0/32 |
| Development | D3 | 21.9% | 4/32 | 25/28 | 0/4 | 0/32 |
| Development | Flat | 12.5% | — | 28/28 | 0/4 | 0/96 |

The flat panel contributes three ballots per trace. A zero denominator means the relevant class was absent.

| Split | Natural traces | J3 fixes | J3 harms | D3 − D2 verdict accuracy (pp) |
| --- | --- | --- | --- | --- |
| Development | 32 | 3 | 0 | +9.38 |

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
| solver | 1024 | 168240 | 6059 | 215.39 |
| j1 | 1024 | 289933 | 6925 | 219.88 |
| j2 | 1024 | 454554 | 13848 | 433.67 |
| j3 | 1024 | 549298 | 13865 | 345.89 |
| development_solver | 64 | 10528 | 365 | 8.36 |

[Machine observations](../../../../results/calibrated/exact-prefix2)
