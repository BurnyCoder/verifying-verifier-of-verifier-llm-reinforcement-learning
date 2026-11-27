# calibrated/top-prefix3

The solver adapter starts from a fresh LoRA initialization with seed 17. Its reward rule is d3. Frozen reviewer calls in order use top-j1, top-j2, exact-j3. The shared architecture, optimizer and sample definition are in the [registered protocol](../../../preregistration.md).

| Run | Updated role | Updates | Development exact | Development n | Held-out exact | Held-out n |
|---|---|---:|---:|---:|---:|---:|
| top-prefix3 | solver | 256 | — | 0 | — | 0 |

### Training generation cost

| Role | Calls | Input tokens | Output tokens | CUDA event seconds |
| --- | --- | --- | --- | --- |
| solver | 1024 | 168240 | 6038 | 218.64 |
| j1 | 1024 | 289924 | 7012 | 243.89 |
| j2 | 1024 | 454631 | 14020 | 480.59 |
| j3 | 1024 | 549547 | 14020 | 496.17 |
| development_solver | 64 | 10528 | 359 | 8.49 |

[Machine observations](../../../../results/calibrated/top-prefix3)
