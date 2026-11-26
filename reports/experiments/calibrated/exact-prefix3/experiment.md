# calibrated/exact-prefix3

The solver adapter starts from a fresh LoRA initialization with seed 17. Its reward rule is d3. Frozen reviewer calls in order use exact-j1, exact-j2, exact-j3. The shared architecture, optimizer and sample definition are in the [registered protocol](../../../preregistration.md).

| Run | Updated role | Updates | Development exact | Development n | Held-out exact | Held-out n |
|---|---|---:|---:|---:|---:|---:|
| exact-prefix3 | solver | 256 | — | 0 | — | 0 |

### Training generation cost

| Role | Calls | Input tokens | Output tokens | CUDA event seconds |
| --- | --- | --- | --- | --- |
| solver | 1024 | 168240 | 6033 | 200.43 |
| j1 | 1024 | 289912 | 6999 | 219.66 |
| j2 | 1024 | 454607 | 13998 | 430.21 |
| j3 | 1024 | 549501 | 13997 | 443.96 |
| development_solver | 64 | 10528 | 347 | 6.87 |

[Machine observations](../../../../results/calibrated/exact-prefix3)
