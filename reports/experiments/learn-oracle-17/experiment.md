# learn-oracle-17

The solver adapter starts from a fresh LoRA initialization with seed 17. Its reward rule is oracle. The exact checker supplies the complete-trace reward. The shared architecture, optimizer and sample definition are in the [registered protocol](../../preregistration.md).

| Run | Updated role | Updates | Development exact | Development n | Held-out exact | Held-out n |
|---|---|---:|---:|---:|---:|---:|
| learn-oracle-17 | solver | 128 | — | 0 | — | 0 |

### Training generation cost

| Role | Calls | Input tokens | Output tokens | CUDA event seconds |
| --- | --- | --- | --- | --- |
| solver | 512 | 84108 | 3025 | 138.45 |
| development_solver | 32 | 5264 | 172 | 4.97 |

[Machine observations](../../../results/learn-oracle-17)
