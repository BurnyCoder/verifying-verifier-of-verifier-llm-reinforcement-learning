# calibrated/exact-depth1

The solver adapter starts from a fresh LoRA initialization with seed 17. Its reward rule is d1. Frozen reviewer calls in order use exact-j1. The shared architecture, optimizer and sample definition are in the [registered protocol](../../../preregistration.md).

| Run | Updated role | Updates | Development exact | Development n | Held-out exact | Held-out n |
|---|---|---:|---:|---:|---:|---:|
| exact-depth1 | solver | 256 | — | 0 | — | 0 |

### Training generation cost

| Role | Calls | Input tokens | Output tokens | CUDA event seconds |
| --- | --- | --- | --- | --- |
| solver | 1024 | 168240 | 6020 | 214.66 |
| j1 | 1024 | 289895 | 7001 | 238.80 |
| development_solver | 64 | 10528 | 352 | 7.59 |

[Machine observations](../../../../results/calibrated/exact-depth1)
