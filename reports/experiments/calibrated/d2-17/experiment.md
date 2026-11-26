# calibrated/d2-17

The solver adapter starts from a fresh LoRA initialization with seed 17. Its reward rule is d2. Frozen reviewer calls in order use the base model, the base model. The shared architecture, optimizer and sample definition are in the [registered protocol](../../../preregistration.md).

| Run | Updated role | Updates | Development exact | Development n | Held-out exact | Held-out n |
|---|---|---:|---:|---:|---:|---:|
| d2-17 | solver | 256 | 78.1% | 32 | — | 0 |

### Replaying the same solver outputs

| Split | Rule | Verdict agreement | Exact evidence / traces | False accepts / invalid | False rejects / valid | Malformed / reports |
| --- | --- | --- | --- | --- | --- | --- |
| Development | D1 | 78.1% | 19/32 | 5/7 | 2/25 | 0/32 |
| Development | D2 | 50.0% | 11/32 | 5/7 | 11/25 | 0/32 |
| Development | D3 | 50.0% | 10/32 | 5/7 | 11/25 | 0/32 |
| Development | Flat | 81.2% | — | 5/7 | 1/25 | 0/96 |

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
| visible | 16 | 15 | 14 | 8 | 0/8 |
| masked | 16 | 10 | 10 | 5 | 0/8 |

These evidence measurements use the identical frozen reviewer from base. They are shared observations.

### Training generation cost

| Role | Calls | Input tokens | Output tokens | CUDA event seconds |
| --- | --- | --- | --- | --- |
| solver | 1024 | 168240 | 6366 | 350.91 |
| j1 | 1024 | 290249 | 6988 | 268.47 |
| j2 | 1024 | 454933 | 13996 | 522.78 |
| development_solver | 64 | 10528 | 383 | 13.54 |

[Machine observations](../../../../results/calibrated/d2-17)
