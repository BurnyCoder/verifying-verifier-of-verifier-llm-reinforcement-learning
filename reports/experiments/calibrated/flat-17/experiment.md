# calibrated/flat-17

The solver adapter starts from a fresh LoRA initialization with seed 17. Its reward rule is flat. Three independent first-order calls vote on the same solver response. The shared architecture, optimizer and sample definition are in the [registered protocol](../../../preregistration.md).

| Run | Updated role | Updates | Development exact | Development n | Held-out exact | Held-out n |
|---|---|---:|---:|---:|---:|---:|
| flat-17 | solver | 256 | — | 0 | — | 0 |

### Training generation cost

| Role | Calls | Input tokens | Output tokens | CUDA event seconds |
| --- | --- | --- | --- | --- |
| solver | 1024 | 168240 | 6126 | 315.73 |
| flat_j1 | 3072 | 870066 | 21037 | 787.36 |
| development_solver | 64 | 10528 | 353 | 11.43 |

[Machine observations](../../../../results/calibrated/flat-17)
