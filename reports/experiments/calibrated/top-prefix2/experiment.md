# calibrated/top-prefix2

The solver adapter starts from a fresh LoRA initialization with seed 17. Its reward rule is d3. Frozen reviewer calls in order use top-j1, top-j2, the base model. The shared architecture, optimizer and sample definition are in the [registered protocol](../../../preregistration.md).

| Run | Updated role | Updates | Development exact | Development n | Held-out exact | Held-out n |
|---|---|---:|---:|---:|---:|---:|
| top-prefix2 | solver | 256 | — | 0 | — | 0 |

### Training generation cost

| Role | Calls | Input tokens | Output tokens | CUDA event seconds |
| --- | --- | --- | --- | --- |
| solver | 1024 | 168240 | 5913 | 187.63 |
| j1 | 1024 | 289803 | 7021 | 218.50 |
| j2 | 1024 | 454519 | 14041 | 432.23 |
| j3 | 1024 | 549456 | 14007 | 338.97 |
| development_solver | 64 | 10528 | 344 | 7.31 |

[Machine observations](../../../../results/calibrated/top-prefix2)
