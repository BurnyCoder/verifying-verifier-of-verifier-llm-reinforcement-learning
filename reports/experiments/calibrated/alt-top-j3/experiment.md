# calibrated/alt-top-j3

The j3 adapter starts from exact-j3 with seed 17. Its reward rule is exact. The judge corpus uses the top-prefix3 solver. The checker labels the complete evidence record. The shared architecture, optimizer and sample definition are in the [registered protocol](../../../preregistration.md).

| Run | Updated role | Updates | Development exact | Development n | Held-out exact | Held-out n |
|---|---|---:|---:|---:|---:|---:|
| alt-top-j3 | j3 | 256 | — | 0 | — | 0 |

### Training generation cost

| Role | Calls | Input tokens | Output tokens | CUDA event seconds |
| --- | --- | --- | --- | --- |
| corpus_solver | 64 | 10517 | 386 | 14.30 |
| j1 | 64 | 18131 | 439 | 15.53 |
| j2 | 64 | 28426 | 878 | 29.86 |
| j3 | 1024 | 549292 | 14044 | 490.22 |

[Machine observations](../../../../results/calibrated/alt-top-j3)
