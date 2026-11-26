# learn-shuffle-17

The solver adapter starts from a fresh LoRA initialization with seed 17. Its reward rule is oracle-shuffle. Frozen reviewer calls in order use the base model, the base model, the base model. The shared architecture, optimizer and sample definition are in the [registered protocol](../../preregistration.md).

| Run | Updated role | Updates | Development exact | Development n | Held-out exact | Held-out n |
|---|---|---:|---:|---:|---:|---:|
| learn-shuffle-17 | solver | 128 | — | 0 | — | 0 |

### Training generation cost

| Role | Calls | Input tokens | Output tokens | CUDA event seconds |
| --- | --- | --- | --- | --- |
| solver | 512 | 84108 | 2968 | 164.88 |
| development_solver | 32 | 5264 | 173 | 5.36 |

[Machine observations](../../../results/learn-shuffle-17)
