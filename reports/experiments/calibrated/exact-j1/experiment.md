# calibrated/exact-j1

The j1 adapter starts from a fresh LoRA initialization with seed 17. Its reward rule is exact. The judge corpus uses the base solver. The checker labels the complete evidence record. The shared architecture, optimizer and sample definition are in the [registered protocol](../../../preregistration.md).

| Run | Updated role | Updates | Development exact | Development n | Held-out exact | Held-out n |
|---|---|---:|---:|---:|---:|---:|
| exact-j1 | j1 | 256 | — | 0 | — | 0 |

### Training generation cost

| Role | Calls | Input tokens | Output tokens | CUDA event seconds |
| --- | --- | --- | --- | --- |
| corpus_solver | 64 | 10517 | 376 | 15.53 |
| j1 | 1088 | 307902 | 7458 | 362.86 |
| j2 | 64 | 28413 | 876 | 33.56 |

[Machine observations](../../../../results/calibrated/exact-j1)
