# calibrated/top-prefix3

The solver adapter starts from a fresh LoRA initialization with seed 17. Its reward rule is d3. Frozen reviewer calls in order use top-j1, top-j2, exact-j3. The shared architecture, optimizer and sample definition are in the [registered protocol](../../../preregistration.md).

| Run | Updated role | Updates | Development exact | Development n | Held-out exact | Held-out n |
|---|---|---:|---:|---:|---:|---:|
| top-prefix3 | solver | 256 | 87.5% | 32 | — | 0 |

### Replaying the same solver outputs

| Split | Rule | Verdict agreement | Exact evidence / traces | False accepts / invalid | False rejects / valid | Malformed / reports |
| --- | --- | --- | --- | --- | --- | --- |
| Development | D1 | 87.5% | 22/32 | 4/4 | 0/28 | 0/32 |
| Development | D2 | 81.2% | 21/32 | 4/4 | 2/28 | 0/32 |
| Development | D3 | 81.2% | 21/32 | 4/4 | 2/28 | 0/32 |
| Development | Flat | 87.5% | — | 4/4 | 0/28 | 0/96 |

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
| solver | 1024 | 168240 | 6038 | 218.64 |
| j1 | 1024 | 289924 | 7012 | 243.89 |
| j2 | 1024 | 454631 | 14020 | 480.59 |
| j3 | 1024 | 549547 | 14020 | 496.17 |
| development_solver | 64 | 10528 | 359 | 8.49 |

[Machine observations](../../../../results/calibrated/top-prefix3)
