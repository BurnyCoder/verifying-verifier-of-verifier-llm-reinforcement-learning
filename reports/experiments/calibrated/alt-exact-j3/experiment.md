# calibrated/alt-exact-j3

The j3 adapter starts from exact-j3 with seed 17. Its reward rule is exact. The judge corpus uses the exact-prefix3 solver. The checker labels the complete evidence record. The shared architecture, optimizer and sample definition are in the [registered protocol](../../../preregistration.md).

| Run | Updated role | Updates | Development exact | Development n | Held-out exact | Held-out n |
|---|---|---:|---:|---:|---:|---:|
| alt-exact-j3 | j3 | 256 | 31.2% | 32 | — | 0 |

### Replaying the same solver outputs

| Split | Rule | Verdict agreement | Exact evidence / traces | False accepts / invalid | False rejects / valid | Malformed / reports |
| --- | --- | --- | --- | --- | --- | --- |
| Development | D1 | 59.4% | 15/32 | 12/12 | 1/20 | 0/32 |
| Development | D2 | 59.4% | 10/32 | 6/12 | 7/20 | 0/32 |
| Development | D3 | 56.2% | 10/32 | 7/12 | 7/20 | 0/32 |
| Development | Flat | 68.8% | — | 10/12 | 0/20 | 0/96 |

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
| visible | 16 | 16 | 16 | 8 | 0/8 |
| masked | 16 | 6 | 6 | 3 | 0/8 |

### Training generation cost

| Role | Calls | Input tokens | Output tokens | CUDA event seconds |
| --- | --- | --- | --- | --- |
| j3 | 1024 | 549256 | 14052 | 547.00 |

[Machine observations](../../../../results/calibrated/alt-exact-j3)
