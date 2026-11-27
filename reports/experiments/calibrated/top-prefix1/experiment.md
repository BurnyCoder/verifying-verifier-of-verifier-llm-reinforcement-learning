# calibrated/top-prefix1

The solver adapter starts from a fresh LoRA initialization with seed 17. Its reward rule is d3. Frozen reviewer calls in order use top-j1, the base model, the base model. The shared architecture, optimizer and sample definition are in the [registered protocol](../../../preregistration.md).

| Run | Updated role | Updates | Development exact | Development n | Held-out exact | Held-out n |
|---|---|---:|---:|---:|---:|---:|
| top-prefix1 | solver | 256 | 6.2% | 32 | — | 0 |

### Replaying the same solver outputs

| Split | Rule | Verdict agreement | Exact evidence / traces | False accepts / invalid | False rejects / valid | Malformed / reports |
| --- | --- | --- | --- | --- | --- | --- |
| Development | D1 | 6.2% | 1/32 | 30/30 | 0/2 | 0/32 |
| Development | D2 | 43.8% | 1/32 | 18/30 | 0/2 | 1/32 |
| Development | D3 | 34.4% | 1/32 | 21/30 | 0/2 | 0/32 |
| Development | Flat | 6.2% | — | 30/30 | 0/2 | 0/96 |

The flat panel contributes three ballots per trace. A zero denominator means the relevant class was absent.

| Split | Natural traces | J3 fixes | J3 harms | D3 − D2 verdict accuracy (pp) |
| --- | --- | --- | --- | --- |
| Development | 32 | 0 | 3 | -9.38 |

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
| solver | 1024 | 168240 | 8405 | 358.98 |
| j1 | 1024 | 292293 | 7039 | 236.79 |
| j2 | 1024 | 457027 | 14222 | 369.94 |
| j3 | 1024 | 552144 | 14197 | 380.41 |
| development_solver | 64 | 10528 | 520 | 16.96 |

[Machine observations](../../../../results/calibrated/top-prefix1)
