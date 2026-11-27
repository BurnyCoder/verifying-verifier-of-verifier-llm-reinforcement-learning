# calibrated/top-prefix1

The solver adapter starts from a fresh LoRA initialization with seed 17. Its reward rule is d3. Frozen reviewer calls in order use top-j1, the base model, the base model. The shared architecture, optimizer and sample definition are in the [registered protocol](../../../preregistration.md).

| Run | Updated role | Updates | Development exact | Development n | Held-out exact | Held-out n |
|---|---|---:|---:|---:|---:|---:|
| top-prefix1 | solver | 256 | — | 0 | — | 0 |

### Training generation cost

| Role | Calls | Input tokens | Output tokens | CUDA event seconds |
| --- | --- | --- | --- | --- |
| solver | 1024 | 168240 | 8405 | 358.98 |
| j1 | 1024 | 292293 | 7039 | 236.79 |
| j2 | 1024 | 457027 | 14222 | 369.94 |
| j3 | 1024 | 552144 | 14197 | 380.41 |
| development_solver | 64 | 10528 | 520 | 16.96 |

[Machine observations](../../../../results/calibrated/top-prefix1)
