# calibrated/top-j1

The j1 adapter starts from a fresh LoRA initialization with seed 17. Its reward rule is teacher. The judge corpus uses the base solver. The frozen teacher is top-j2. The shared architecture, optimizer and sample definition are in the [registered protocol](../../../preregistration.md).

| Run | Updated role | Updates | Development exact | Development n | Held-out exact | Held-out n |
|---|---|---:|---:|---:|---:|---:|
| top-j1 | j1 | 256 | 50.0% | 32 | — | 0 |

### Replaying the same solver outputs

| Split | Rule | Verdict agreement | Exact evidence / traces | False accepts / invalid | False rejects / valid | Malformed / reports |
| --- | --- | --- | --- | --- | --- | --- |
| Development | D1 | 62.5% | 16/32 | 12/12 | 0/20 | 0/32 |
| Development | D2 | 62.5% | 11/32 | 6/12 | 6/20 | 0/32 |
| Development | D3 | 56.2% | 10/32 | 8/12 | 6/20 | 0/32 |
| Development | Flat | 62.5% | — | 12/12 | 0/20 | 0/96 |

The flat panel contributes three ballots per trace. A zero denominator means the relevant class was absent.

| Split | Natural traces | J3 fixes | J3 harms | D3 − D2 verdict accuracy (pp) |
| --- | --- | --- | --- | --- |
| Development | 32 | 0 | 2 | -6.25 |

### Training generation cost

| Role | Calls | Input tokens | Output tokens | CUDA event seconds |
| --- | --- | --- | --- | --- |
| j1 | 1024 | 289784 | 7015 | 231.50 |
| j2 | 1024 | 454495 | 14030 | 451.05 |

[Machine observations](../../../../results/calibrated/top-j1)
