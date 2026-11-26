# calibrated/d2-17

The solver adapter starts from a fresh LoRA initialization with seed 17. Its reward rule is d2. Frozen reviewer calls in order use the base model, the base model. The shared architecture, optimizer and sample definition are in the [registered protocol](../../../preregistration.md).

| Run | Updated role | Updates | Development exact | Development n | Held-out exact | Held-out n |
|---|---|---:|---:|---:|---:|---:|
| d2-17 | solver | 256 | — | 0 | — | 0 |

### Training generation cost

| Role | Calls | Input tokens | Output tokens | CUDA event seconds |
| --- | --- | --- | --- | --- |
| solver | 1024 | 168240 | 6366 | 350.91 |
| j1 | 1024 | 290249 | 6988 | 268.47 |
| j2 | 1024 | 454933 | 13996 | 522.78 |
| development_solver | 64 | 10528 | 383 | 13.54 |

[Machine observations](../../../../results/calibrated/d2-17)
