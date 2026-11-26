# calibrated/exact-prefix1

The solver adapter starts from a fresh LoRA initialization with seed 17. Its reward rule is d3. Frozen reviewer calls in order use exact-j1, the base model, the base model. The shared architecture, optimizer and sample definition are in the [registered protocol](../../../preregistration.md).

| Run | Updated role | Updates | Development exact | Development n | Held-out exact | Held-out n |
|---|---|---:|---:|---:|---:|---:|
| exact-prefix1 | solver | 256 | 75.0% | 32 | — | 0 |

### Replaying the same solver outputs

| Split | Rule | Verdict agreement | Exact evidence / traces | False accepts / invalid | False rejects / valid | Malformed / reports |
| --- | --- | --- | --- | --- | --- | --- |
| Development | D1 | 75.0% | 24/32 | 8/8 | 0/24 | 0/32 |
| Development | D2 | 43.8% | 14/32 | 8/8 | 10/24 | 0/32 |
| Development | D3 | 40.6% | 12/32 | 8/8 | 11/24 | 0/32 |
| Development | Flat | 75.0% | — | 8/8 | 0/24 | 0/96 |

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
| solver | 1024 | 168240 | 6194 | 214.68 |
| j1 | 1024 | 290073 | 6990 | 222.66 |
| j2 | 1024 | 454759 | 13967 | 335.78 |
| j3 | 1024 | 549622 | 13987 | 352.22 |
| development_solver | 64 | 10528 | 369 | 8.17 |

[Machine observations](../../../../results/calibrated/exact-prefix1)
