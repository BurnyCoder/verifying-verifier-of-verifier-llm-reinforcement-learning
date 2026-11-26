# calibrated/d3-17

The solver adapter starts from a fresh LoRA initialization with seed 17. Its reward rule is d3. Frozen reviewer calls in order use the base model, the base model, the base model. The shared architecture, optimizer and sample definition are in the [registered protocol](../../../preregistration.md).

| Run | Updated role | Updates | Development exact | Development n | Held-out exact | Held-out n |
|---|---|---:|---:|---:|---:|---:|
| d3-17 | solver | 256 | 9.4% | 32 | — | 0 |

### Replaying the same solver outputs

| Split | Rule | Verdict agreement | Exact evidence / traces | False accepts / invalid | False rejects / valid | Malformed / reports |
| --- | --- | --- | --- | --- | --- | --- |
| Development | D1 | 12.5% | 3/32 | 28/29 | 0/3 | 0/32 |
| Development | D2 | 37.5% | 2/32 | 19/29 | 1/3 | 0/32 |
| Development | D3 | 37.5% | 2/32 | 19/29 | 1/3 | 0/32 |
| Development | Flat | 15.6% | — | 27/29 | 0/3 | 0/96 |

The flat panel contributes three ballots per trace. A zero denominator means the relevant class was absent.

| Split | Natural traces | J3 fixes | J3 harms | D3 − D2 verdict accuracy (pp) |
| --- | --- | --- | --- | --- |
| Development | 32 | 1 | 1 | +0.00 |

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
| solver | 1024 | 168240 | 6141 | 345.31 |
| j1 | 1024 | 290006 | 6889 | 260.46 |
| j2 | 1024 | 454591 | 13813 | 514.35 |
| j3 | 1024 | 549299 | 13868 | 559.61 |
| development_solver | 64 | 10528 | 352 | 12.25 |

[Machine observations](../../../../results/calibrated/d3-17)
