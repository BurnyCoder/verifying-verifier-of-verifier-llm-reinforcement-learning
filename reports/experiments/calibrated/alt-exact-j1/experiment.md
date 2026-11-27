# calibrated/alt-exact-j1

The j1 adapter starts from exact-j1 with seed 17. Its reward rule is exact. The judge corpus uses the exact-prefix3 solver. The checker labels the complete evidence record. The shared architecture, optimizer and sample definition are in the [registered protocol](../../../preregistration.md).

| Run | Updated role | Updates | Development exact | Development n | Held-out exact | Held-out n |
|---|---|---:|---:|---:|---:|---:|
| alt-exact-j1 | j1 | 256 | — | 0 | — | 0 |

### Training generation cost

| Role | Calls | Input tokens | Output tokens | CUDA event seconds |
| --- | --- | --- | --- | --- |
| corpus_solver | 64 | 10517 | 376 | 13.52 |
| j1 | 1088 | 307907 | 7454 | 258.55 |
| j2 | 64 | 28415 | 880 | 30.22 |

[Machine observations](../../../../results/calibrated/alt-exact-j1)
