# calibrated/exact-prefix1

The solver adapter starts from a fresh LoRA initialization with seed 17. Its reward rule is d3. Frozen reviewer calls in order use exact-j1, the base model, the base model. The shared architecture, optimizer and sample definition are in the [registered protocol](../../../preregistration.md).

| Run | Updated role | Updates | Development exact | Development n | Held-out exact | Held-out n |
|---|---|---:|---:|---:|---:|---:|
| exact-prefix1 | solver | 256 | — | 0 | — | 0 |

### Training generation cost

| Role | Calls | Input tokens | Output tokens | CUDA event seconds |
| --- | --- | --- | --- | --- |
| solver | 1024 | 168240 | 6194 | 214.68 |
| j1 | 1024 | 290073 | 6990 | 222.66 |
| j2 | 1024 | 454759 | 13967 | 335.78 |
| j3 | 1024 | 549622 | 13987 | 352.22 |
| development_solver | 64 | 10528 | 369 | 8.17 |

[Machine observations](../../../../results/calibrated/exact-prefix1)
