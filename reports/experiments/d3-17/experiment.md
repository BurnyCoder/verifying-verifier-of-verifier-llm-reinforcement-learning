# d3-17

The solver adapter starts from a fresh LoRA initialization with seed 17. Its reward rule is d3. Frozen reviewer calls in order use the base model, the base model, the base model. The shared architecture, optimizer and sample definition are in the [registered protocol](../../preregistration.md).

| Run | Updated role | Updates | Development exact | Development n | Held-out exact | Held-out n |
|---|---|---:|---:|---:|---:|---:|
| d3-17 | solver | 256 | — | 0 | — | 0 |

### Training generation cost

| Role | Calls | Input tokens | Output tokens | CUDA event seconds |
| --- | --- | --- | --- | --- |
| solver | 1024 | 104140 | 34481 | 2031.91 |
| j1 | 1024 | 216588 | 7155 | 367.75 |
| j2 | 1024 | 334167 | 24943 | 1551.79 |
| j3 | 1024 | 364396 | 23000 | 1450.66 |
| development_solver | 64 | 6304 | 2161 | 80.14 |

[Machine observations](../../../results/d3-17)
