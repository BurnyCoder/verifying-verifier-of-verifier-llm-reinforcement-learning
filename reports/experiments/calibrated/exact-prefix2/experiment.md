# calibrated/exact-prefix2

The solver adapter starts from a fresh LoRA initialization with seed 17. Its reward rule is d3. Frozen reviewer calls in order use exact-j1, exact-j2, the base model. The shared architecture, optimizer and sample definition are in the [registered protocol](../../../preregistration.md).

| Run | Updated role | Updates | Development exact | Development n | Held-out exact | Held-out n |
|---|---|---:|---:|---:|---:|---:|
| exact-prefix2 | solver | 256 | — | 0 | — | 0 |

### Training generation cost

| Role | Calls | Input tokens | Output tokens | CUDA event seconds |
| --- | --- | --- | --- | --- |
| solver | 1024 | 168240 | 6059 | 215.39 |
| j1 | 1024 | 289933 | 6925 | 219.88 |
| j2 | 1024 | 454554 | 13848 | 433.67 |
| j3 | 1024 | 549298 | 13865 | 345.89 |
| development_solver | 64 | 10528 | 365 | 8.36 |

[Machine observations](../../../../results/calibrated/exact-prefix2)
