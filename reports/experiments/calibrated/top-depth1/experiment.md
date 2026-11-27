# calibrated/top-depth1

The solver adapter starts from a fresh LoRA initialization with seed 17. Its reward rule is d1. Frozen reviewer calls in order use top-j1. The shared architecture, optimizer and sample definition are in the [registered protocol](../../../preregistration.md).

| Run | Updated role | Updates | Development exact | Development n | Held-out exact | Held-out n |
|---|---|---:|---:|---:|---:|---:|
| top-depth1 | solver | 256 | — | 0 | — | 0 |

### Training generation cost

| Role | Calls | Input tokens | Output tokens | CUDA event seconds |
| --- | --- | --- | --- | --- |
| solver | 1024 | 168240 | 5989 | 206.39 |
| j1 | 1024 | 289863 | 7002 | 235.14 |
| development_solver | 64 | 10528 | 353 | 7.55 |

[Machine observations](../../../../results/calibrated/top-depth1)
