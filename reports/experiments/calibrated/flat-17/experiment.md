# calibrated/flat-17

The solver adapter starts from a fresh LoRA initialization with seed 17. Its reward rule is flat. Three independent first-order calls vote on the same solver response. The shared architecture, optimizer and sample definition are in the [registered protocol](../../../preregistration.md).

| Run | Updated role | Updates | Development exact | Development n | Held-out exact | Held-out n |
|---|---|---:|---:|---:|---:|---:|
| flat-17 | solver | 256 | 75.0% | 32 | — | 0 |

### Replaying the same solver outputs

| Split | Rule | Verdict agreement | Exact evidence / traces | False accepts / invalid | False rejects / valid | Malformed / reports |
| --- | --- | --- | --- | --- | --- | --- |
| Development | D1 | 84.4% | 20/32 | 5/8 | 0/24 | 0/32 |
| Development | D2 | 59.4% | 11/32 | 5/8 | 8/24 | 0/32 |
| Development | D3 | 56.2% | 10/32 | 5/8 | 9/24 | 1/32 |
| Development | Flat | 84.4% | — | 5/8 | 0/24 | 0/96 |

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
| solver | 1024 | 168240 | 6126 | 315.73 |
| flat_j1 | 3072 | 870066 | 21037 | 787.36 |
| development_solver | 64 | 10528 | 353 | 11.43 |

[Machine observations](../../../../results/calibrated/flat-17)
