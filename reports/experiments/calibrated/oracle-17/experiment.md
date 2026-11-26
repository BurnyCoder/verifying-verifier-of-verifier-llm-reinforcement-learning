# calibrated/oracle-17

The solver adapter starts from a fresh LoRA initialization with seed 17. Its reward rule is oracle. The exact checker supplies the complete-trace reward. The shared architecture, optimizer and sample definition are in the [registered protocol](../../../preregistration.md).

| Run | Updated role | Updates | Development exact | Development n | Held-out exact | Held-out n |
|---|---|---:|---:|---:|---:|---:|
| oracle-17 | solver | 256 | 100.0% | 32 | — | 0 |

### Replaying the same solver outputs

| Split | Rule | Verdict agreement | Exact evidence / traces | False accepts / invalid | False rejects / valid | Malformed / reports |
| --- | --- | --- | --- | --- | --- | --- |
| Development | D1 | 87.5% | 22/32 | 0/0 | 4/32 | 0/32 |
| Development | D2 | 59.4% | 14/32 | 0/0 | 13/32 | 0/32 |
| Development | D3 | 59.4% | 13/32 | 0/0 | 13/32 | 0/32 |
| Development | Flat | 90.6% | — | 0/0 | 3/32 | 0/96 |

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
| solver | 1024 | 168240 | 6079 | 304.09 |
| development_solver | 64 | 10528 | 346 | 11.54 |

[Machine observations](../../../../results/calibrated/oracle-17)
