# d3-17

The solver adapter starts from a fresh LoRA initialization with seed 17. Its reward rule is d3. Frozen reviewer calls in order use the base model, the base model, the base model. The shared architecture, optimizer and sample definition are in the [registered protocol](../../preregistration.md).

| Run | Updated role | Updates | Development exact | Development n | Held-out exact | Held-out n |
|---|---|---:|---:|---:|---:|---:|
| d3-17 | solver | 256 | 0.0% | 32 | — | 0 |

### Replaying the same solver outputs

| Split | Rule | Verdict agreement | Exact evidence / traces | False accepts / invalid | False rejects / valid | Malformed / reports |
| --- | --- | --- | --- | --- | --- | --- |
| Development | D1 | 100.0% | 0/32 | 0/32 | 0/0 | 32/32 |
| Development | D2 | 100.0% | 0/32 | 0/32 | 0/0 | 22/32 |
| Development | D3 | 100.0% | 0/32 | 0/32 | 0/0 | 23/32 |
| Development | Flat | 100.0% | — | 0/32 | 0/0 | 87/96 |

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
| visible | 16 | 2 | 2 | 1 | 0/8 |
| masked | 16 | 6 | 4 | 3 | 0/8 |

These evidence measurements use the identical frozen reviewer from base. They are shared observations.

### Training generation cost

| Role | Calls | Input tokens | Output tokens | CUDA event seconds |
| --- | --- | --- | --- | --- |
| solver | 1024 | 104140 | 34481 | 2031.91 |
| j1 | 1024 | 216588 | 7155 | 367.75 |
| j2 | 1024 | 334167 | 24943 | 1551.79 |
| j3 | 1024 | 364396 | 23000 | 1450.66 |
| development_solver | 64 | 6304 | 2161 | 80.14 |

[Machine observations](../../../results/d3-17)
