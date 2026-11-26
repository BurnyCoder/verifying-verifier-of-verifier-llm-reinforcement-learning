# calibrated/oracle-17

The solver adapter starts from a fresh LoRA initialization with seed 17. Its reward rule is oracle. The exact checker supplies the complete-trace reward. The shared architecture, optimizer and sample definition are in the [registered protocol](../../../preregistration.md).

| Run | Updated role | Updates | Development exact | Development n | Held-out exact | Held-out n |
|---|---|---:|---:|---:|---:|---:|
| oracle-17 | solver | 256 | — | 0 | — | 0 |

### Training generation cost

| Role | Calls | Input tokens | Output tokens | CUDA event seconds |
| --- | --- | --- | --- | --- |
| solver | 1024 | 168240 | 6079 | 304.09 |
| development_solver | 64 | 10528 | 346 | 11.54 |

[Machine observations](../../../../results/calibrated/oracle-17)
