# calibrated/d1-17

The solver adapter starts from a fresh LoRA initialization with seed 17. Its reward rule is d1. Frozen reviewer calls in order use the base model. The shared architecture, optimizer and sample definition are in the [registered protocol](../../../preregistration.md).

| Run | Updated role | Updates | Development exact | Development n | Held-out exact | Held-out n |
|---|---|---:|---:|---:|---:|---:|
| d1-17 | solver | 256 | — | 0 | — | 0 |

### Training generation cost

| Role | Calls | Input tokens | Output tokens | CUDA event seconds |
| --- | --- | --- | --- | --- |
| solver | 1024 | 168240 | 6020 | 305.49 |
| j1 | 1024 | 289892 | 6992 | 263.53 |
| development_solver | 64 | 10528 | 353 | 12.39 |

[Machine observations](../../../../results/calibrated/d1-17)
