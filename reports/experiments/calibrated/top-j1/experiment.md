# calibrated/top-j1

The j1 adapter starts from a fresh LoRA initialization with seed 17. Its reward rule is teacher. The judge corpus uses the base solver. The frozen teacher is top-j2. The shared architecture, optimizer and sample definition are in the [registered protocol](../../../preregistration.md).

| Run | Updated role | Updates | Development exact | Development n | Held-out exact | Held-out n |
|---|---|---:|---:|---:|---:|---:|
| top-j1 | j1 | 256 | — | 0 | — | 0 |

### Training generation cost

| Role | Calls | Input tokens | Output tokens | CUDA event seconds |
| --- | --- | --- | --- | --- |
| j1 | 1024 | 289784 | 7015 | 231.50 |
| j2 | 1024 | 454495 | 14030 | 451.05 |

[Machine observations](../../../../results/calibrated/top-j1)
