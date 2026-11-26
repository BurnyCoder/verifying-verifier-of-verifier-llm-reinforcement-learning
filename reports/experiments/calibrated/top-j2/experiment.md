# calibrated/top-j2

The j2 adapter starts from a fresh LoRA initialization with seed 17. Its reward rule is teacher. The judge corpus uses the base solver. The frozen teacher is exact-j3. The shared architecture, optimizer and sample definition are in the [registered protocol](../../../preregistration.md).

| Run | Updated role | Updates | Development exact | Development n | Held-out exact | Held-out n |
|---|---|---:|---:|---:|---:|---:|
| top-j2 | j2 | 256 | — | 0 | — | 0 |

### Training generation cost

| Role | Calls | Input tokens | Output tokens | CUDA event seconds |
| --- | --- | --- | --- | --- |
| j2 | 1024 | 454500 | 14015 | 572.40 |
| j3 | 1024 | 549411 | 14075 | 556.99 |

[Machine observations](../../../../results/calibrated/top-j2)
