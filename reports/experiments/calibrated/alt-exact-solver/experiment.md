# calibrated/alt-exact-solver

The solver adapter starts from exact-prefix3 with seed 17. Its reward rule is d3. Frozen reviewer calls in order use alt-exact-j1, alt-exact-j2, alt-exact-j3. The shared architecture, optimizer and sample definition are in the [registered protocol](../../../preregistration.md).

| Run | Updated role | Updates | Development exact | Development n | Held-out exact | Held-out n |
|---|---|---:|---:|---:|---:|---:|
| alt-exact-solver | solver | 256 | — | 0 | — | 0 |

### Training generation cost

| Role | Calls | Input tokens | Output tokens | CUDA event seconds |
| --- | --- | --- | --- | --- |
| solver | 1024 | 168240 | 6016 | 245.03 |
| j1 | 1024 | 289884 | 6985 | 260.69 |
| j2 | 1024 | 454565 | 13970 | 520.75 |
| j3 | 1024 | 549431 | 13970 | 534.72 |
| development_solver | 64 | 10528 | 345 | 8.64 |

[Machine observations](../../../../results/calibrated/alt-exact-solver)
