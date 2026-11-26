# calibrated/hybrid-17

The solver adapter starts from a fresh LoRA initialization with seed 17. Its reward rule is hybrid. Frozen reviewer calls in order use the base model, the base model, the base model. The shared architecture, optimizer and sample definition are in the [registered protocol](../../../preregistration.md).

| Run | Updated role | Updates | Development exact | Development n | Held-out exact | Held-out n |
|---|---|---:|---:|---:|---:|---:|
| hybrid-17 | solver | 256 | 96.9% | 32 | — | 0 |

### Replaying the same solver outputs

| Split | Rule | Verdict agreement | Exact evidence / traces | False accepts / invalid | False rejects / valid | Malformed / reports |
| --- | --- | --- | --- | --- | --- | --- |
| Development | D1 | 84.4% | 21/32 | 1/1 | 4/31 | 0/32 |
| Development | D2 | 56.2% | 13/32 | 1/1 | 13/31 | 0/32 |
| Development | D3 | 53.1% | 12/32 | 1/1 | 14/31 | 0/32 |
| Development | Flat | 87.5% | — | 1/1 | 3/31 | 0/96 |

The flat panel contributes three ballots per trace. A zero denominator means the relevant class was absent.

| Split | Natural traces | J3 fixes | J3 harms | D3 − D2 verdict accuracy (pp) |
| --- | --- | --- | --- | --- |
| Development | 32 | 0 | 1 | -3.12 |

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
| solver | 1024 | 168240 | 6101 | 303.07 |
| j1 | 1024 | 289996 | 7006 | 263.78 |
| j2 | 1024 | 454698 | 13986 | 507.36 |
| j3 | 1024 | 549580 | 14048 | 541.96 |
| development_solver | 64 | 10528 | 354 | 11.26 |

[Machine observations](../../../../results/calibrated/hybrid-17)
