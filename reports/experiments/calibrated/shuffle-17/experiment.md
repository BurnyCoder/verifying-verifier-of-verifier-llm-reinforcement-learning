# calibrated/shuffle-17

The solver adapter starts from a fresh LoRA initialization with seed 17. Its reward rule is shuffle. Frozen reviewer calls in order use the base model, the base model, the base model. The shared architecture, optimizer and sample definition are in the [registered protocol](../../../preregistration.md).

| Run | Updated role | Updates | Development exact | Development n | Held-out exact | Held-out n |
|---|---|---:|---:|---:|---:|---:|
| shuffle-17 | solver | 256 | — | 0 | — | 0 |

### Training generation cost

| Role | Calls | Input tokens | Output tokens | CUDA event seconds |
| --- | --- | --- | --- | --- |
| solver | 1024 | 168240 | 5941 | 296.37 |
| j1 | 1024 | 289832 | 6995 | 259.62 |
| j2 | 1024 | 454523 | 13985 | 502.64 |
| j3 | 1024 | 549404 | 14017 | 536.31 |
| development_solver | 64 | 10528 | 344 | 11.53 |

[Machine observations](../../../../results/calibrated/shuffle-17)
