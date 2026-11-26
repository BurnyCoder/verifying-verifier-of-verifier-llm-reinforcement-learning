# calibrated/exact-prefix3

The solver adapter starts from a fresh LoRA initialization with seed 17. Its reward rule is d3. Frozen reviewer calls in order use exact-j1, exact-j2, exact-j3. The shared architecture, optimizer and sample definition are in the [registered protocol](../../../preregistration.md).

| Run | Updated role | Updates | Development exact | Development n | Held-out exact | Held-out n |
|---|---|---:|---:|---:|---:|---:|
| exact-prefix3 | solver | 256 | 78.1% | 32 | — | 0 |

### Replaying the same solver outputs

| Split | Rule | Verdict agreement | Exact evidence / traces | False accepts / invalid | False rejects / valid | Malformed / reports |
| --- | --- | --- | --- | --- | --- | --- |
| Development | D1 | 78.1% | 25/32 | 7/7 | 0/25 | 0/32 |
| Development | D2 | 78.1% | 25/32 | 7/7 | 0/25 | 0/32 |
| Development | D3 | 78.1% | 25/32 | 7/7 | 0/25 | 0/32 |
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
| solver | 1024 | 168240 | 6033 | 200.43 |
| j1 | 1024 | 289912 | 6999 | 219.66 |
| j2 | 1024 | 454607 | 13998 | 430.21 |
| j3 | 1024 | 549501 | 13997 | 443.96 |
| development_solver | 64 | 10528 | 347 | 6.87 |

[Machine observations](../../../../results/calibrated/exact-prefix3)
