# calibrated/d3-17

The solver adapter starts from a fresh LoRA initialization with seed 17. Its reward rule is d3. Frozen reviewer calls in order use the base model, the base model, the base model. The shared architecture, optimizer and sample definition are in the [registered protocol](../../../preregistration.md).

| Run | Updated role | Updates | Development exact | Development n | Held-out exact | Held-out n |
|---|---|---:|---:|---:|---:|---:|
| d3-17 | solver | 256 | — | 0 | — | 0 |

### Training generation cost

| Role | Calls | Input tokens | Output tokens | CUDA event seconds |
| --- | --- | --- | --- | --- |
| solver | 1024 | 168240 | 6141 | 345.31 |
| j1 | 1024 | 290006 | 6889 | 260.46 |
| j2 | 1024 | 454591 | 13813 | 514.35 |
| j3 | 1024 | 549299 | 13868 | 559.61 |
| development_solver | 64 | 10528 | 352 | 12.25 |

[Machine observations](../../../../results/calibrated/d3-17)
