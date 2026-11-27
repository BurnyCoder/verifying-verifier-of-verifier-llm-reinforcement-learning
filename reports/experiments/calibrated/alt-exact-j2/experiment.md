# calibrated/alt-exact-j2

The j2 adapter starts from exact-j2 with seed 17. Its reward rule is exact. The judge corpus uses the exact-prefix3 solver. The checker labels the complete evidence record. The shared architecture, optimizer and sample definition are in the [registered protocol](../../../preregistration.md).

| Run | Updated role | Updates | Development exact | Development n | Held-out exact | Held-out n |
|---|---|---:|---:|---:|---:|---:|
| alt-exact-j2 | j2 | 256 | 46.9% | 32 | — | 0 |

### Replaying the same solver outputs

| Split | Rule | Verdict agreement | Exact evidence / traces | False accepts / invalid | False rejects / valid | Malformed / reports |
| --- | --- | --- | --- | --- | --- | --- |
| Development | D1 | 59.4% | 15/32 | 12/12 | 1/20 | 0/32 |
| Development | D2 | 59.4% | 15/32 | 12/12 | 1/20 | 0/32 |
| Development | D3 | 59.4% | 14/32 | 12/12 | 1/20 | 0/32 |
| Development | Flat | 68.8% | — | 10/12 | 0/20 | 0/96 |

The flat panel contributes three ballots per trace. A zero denominator means the relevant class was absent.

| Split | Natural traces | J3 fixes | J3 harms | D3 − D2 verdict accuracy (pp) |
| --- | --- | --- | --- | --- |
| Development | 32 | 0 | 0 | +0.00 |

### Training generation cost

| Role | Calls | Input tokens | Output tokens | CUDA event seconds |
| --- | --- | --- | --- | --- |
| j2 | 1024 | 454508 | 14048 | 541.04 |

[Machine observations](../../../../results/calibrated/alt-exact-j2)
