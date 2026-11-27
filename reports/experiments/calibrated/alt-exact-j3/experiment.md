# calibrated/alt-exact-j3

The j3 adapter starts from exact-j3 with seed 17. Its reward rule is exact. The judge corpus uses the exact-prefix3 solver. The checker labels the complete evidence record. The shared architecture, optimizer and sample definition are in the [registered protocol](../../../preregistration.md).

| Run | Updated role | Updates | Development exact | Development n | Held-out exact | Held-out n |
|---|---|---:|---:|---:|---:|---:|
| alt-exact-j3 | j3 | 256 | — | 0 | — | 0 |

### Training generation cost

| Role | Calls | Input tokens | Output tokens | CUDA event seconds |
| --- | --- | --- | --- | --- |
| j3 | 1024 | 549256 | 14052 | 547.00 |

[Machine observations](../../../../results/calibrated/alt-exact-j3)
