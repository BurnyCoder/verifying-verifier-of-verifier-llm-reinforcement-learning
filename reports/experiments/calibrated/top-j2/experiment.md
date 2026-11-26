# calibrated/top-j2

The j2 adapter starts from a fresh LoRA initialization with seed 17. Its reward rule is teacher. The judge corpus uses the base solver. The frozen teacher is exact-j3. The shared architecture, optimizer and sample definition are in the [registered protocol](../../../preregistration.md).

| Run | Updated role | Updates | Development exact | Development n | Held-out exact | Held-out n |
|---|---|---:|---:|---:|---:|---:|
| top-j2 | j2 | 256 | 43.8% | 32 | — | 0 |

### Replaying the same solver outputs

| Split | Rule | Verdict agreement | Exact evidence / traces | False accepts / invalid | False rejects / valid | Malformed / reports |
| --- | --- | --- | --- | --- | --- | --- |
| Development | D1 | 59.4% | 15/32 | 12/12 | 1/20 | 0/32 |
| Development | D2 | 59.4% | 14/32 | 11/12 | 2/20 | 0/32 |
| Development | D3 | 56.2% | 13/32 | 11/12 | 3/20 | 0/32 |
| Development | Flat | 68.8% | — | 10/12 | 0/20 | 0/96 |

The flat panel contributes three ballots per trace. A zero denominator means the relevant class was absent.

| Split | Natural traces | J3 fixes | J3 harms | D3 − D2 verdict accuracy (pp) |
| --- | --- | --- | --- | --- |
| Development | 32 | 0 | 1 | -3.12 |

### Training generation cost

| Role | Calls | Input tokens | Output tokens | CUDA event seconds |
| --- | --- | --- | --- | --- |
| j2 | 1024 | 454500 | 14015 | 572.40 |
| j3 | 1024 | 549411 | 14075 | 556.99 |

[Machine observations](../../../../results/calibrated/top-j2)
