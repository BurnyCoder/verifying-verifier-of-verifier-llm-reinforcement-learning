# calibrated/top-prefix2

The solver adapter starts from a fresh LoRA initialization with seed 17. Its reward rule is d3. Frozen reviewer calls in order use top-j1, top-j2, the base model. The shared architecture, optimizer and sample definition are in the [registered protocol](../../../preregistration.md).

| Run | Updated role | Updates | Development exact | Development n | Held-out exact | Held-out n |
|---|---|---:|---:|---:|---:|---:|
| top-prefix2 | solver | 256 | 96.9% | 32 | — | 0 |

### Replaying the same solver outputs

| Split | Rule | Verdict agreement | Exact evidence / traces | False accepts / invalid | False rejects / valid | Malformed / reports |
| --- | --- | --- | --- | --- | --- | --- |
| Development | D1 | 96.9% | 24/32 | 1/1 | 0/31 | 0/32 |
| Development | D2 | 90.6% | 23/32 | 1/1 | 2/31 | 0/32 |
| Development | D3 | 84.4% | 21/32 | 1/1 | 4/31 | 1/32 |
| Development | Flat | 96.9% | — | 1/1 | 0/31 | 0/96 |

The flat panel contributes three ballots per trace. A zero denominator means the relevant class was absent.

| Split | Natural traces | J3 fixes | J3 harms | D3 − D2 verdict accuracy (pp) |
| --- | --- | --- | --- | --- |
| Development | 32 | 0 | 2 | -6.25 |

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
| solver | 1024 | 168240 | 5913 | 187.63 |
| j1 | 1024 | 289803 | 7021 | 218.50 |
| j2 | 1024 | 454519 | 14041 | 432.23 |
| j3 | 1024 | 549456 | 14007 | 338.97 |
| development_solver | 64 | 10528 | 344 | 7.31 |

[Machine observations](../../../../results/calibrated/top-prefix2)
