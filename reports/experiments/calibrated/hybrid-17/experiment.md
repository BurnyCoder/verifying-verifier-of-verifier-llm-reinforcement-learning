# calibrated/hybrid-17

The solver adapter starts from a fresh LoRA initialization with seed 17. Its reward rule is hybrid. Frozen reviewer calls in order use the base model, the base model, the base model. The shared architecture, optimizer and sample definition are in the [registered protocol](../../../preregistration.md).

| Run | Updated role | Updates | Development exact | Development n | Held-out exact | Held-out n |
|---|---|---:|---:|---:|---:|---:|
| hybrid-17 | solver | 256 | — | 0 | — | 0 |

### Training generation cost

| Role | Calls | Input tokens | Output tokens | CUDA event seconds |
| --- | --- | --- | --- | --- |
| solver | 1024 | 168240 | 6101 | 303.07 |
| j1 | 1024 | 289996 | 7006 | 263.78 |
| j2 | 1024 | 454698 | 13986 | 507.36 |
| j3 | 1024 | 549580 | 14048 | 541.96 |
| development_solver | 64 | 10528 | 354 | 11.26 |

[Machine observations](../../../../results/calibrated/hybrid-17)
