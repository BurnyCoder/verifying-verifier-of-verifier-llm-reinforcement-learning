# calibrated/exact-j1

The j1 adapter starts from a fresh LoRA initialization with seed 17. Its reward rule is exact. The judge corpus uses the base solver. The checker labels the complete evidence record. The shared architecture, optimizer and sample definition are in the [registered protocol](../../../preregistration.md).

| Run | Updated role | Updates | Development exact | Development n | Held-out exact | Held-out n |
|---|---|---:|---:|---:|---:|---:|
| exact-j1 | j1 | 256 | 62.5% | 32 | — | 0 |

### Replaying the same solver outputs

| Split | Rule | Verdict agreement | Exact evidence / traces | False accepts / invalid | False rejects / valid | Malformed / reports |
| --- | --- | --- | --- | --- | --- | --- |
| Development | D1 | 62.5% | 20/32 | 12/12 | 0/20 | 0/32 |
| Development | D2 | 62.5% | 14/32 | 6/12 | 6/20 | 0/32 |
| Development | D3 | 59.4% | 13/32 | 7/12 | 6/20 | 0/32 |
| Development | Flat | 62.5% | — | 12/12 | 0/20 | 0/96 |

The flat panel contributes three ballots per trace. A zero denominator means the relevant class was absent.

| Split | Natural traces | J3 fixes | J3 harms | D3 − D2 verdict accuracy (pp) |
| --- | --- | --- | --- | --- |
| Development | 32 | 0 | 1 | -3.12 |

### Training generation cost

| Role | Calls | Input tokens | Output tokens | CUDA event seconds |
| --- | --- | --- | --- | --- |
| corpus_solver | 64 | 10517 | 376 | 15.53 |
| j1 | 1088 | 307902 | 7458 | 362.86 |
| j2 | 64 | 28413 | 876 | 33.56 |

[Machine observations](../../../../results/calibrated/exact-j1)
