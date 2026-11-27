# calibrated/exact-depth2

The solver adapter starts from a fresh LoRA initialization with seed 17. Its reward rule is d2. Frozen reviewer calls in order use exact-j1, exact-j2. The shared architecture, optimizer and sample definition are in the [registered protocol](../../../preregistration.md).

| Run | Updated role | Updates | Development exact | Development n | Held-out exact | Held-out n |
|---|---|---:|---:|---:|---:|---:|
| exact-depth2 | solver | 256 | — | 0 | — | 0 |

### Training generation cost

| Role | Calls | Input tokens | Output tokens | CUDA event seconds |
| --- | --- | --- | --- | --- |
| solver | 1024 | 168240 | 6020 | 224.88 |
| j1 | 1024 | 289895 | 7001 | 244.31 |
| j2 | 1024 | 454592 | 14002 | 482.85 |
| development_solver | 64 | 10528 | 352 | 7.41 |

[Machine observations](../../../../results/calibrated/exact-depth2)
