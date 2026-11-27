# calibrated/alt-exact-solver

The solver adapter starts from exact-prefix3 with seed 17. Its reward rule is d3. Frozen reviewer calls in order use alt-exact-j1, alt-exact-j2, alt-exact-j3. The shared architecture, optimizer and sample definition are in the [registered protocol](../../../preregistration.md).

| Run | Updated role | Updates | Development exact | Development n | Held-out exact | Held-out n |
|---|---|---:|---:|---:|---:|---:|
| alt-exact-solver | solver | 256 | 6.2% | 32 | — | 0 |

### Replaying the same solver outputs

| Split | Rule | Verdict agreement | Exact evidence / traces | False accepts / invalid | False rejects / valid | Malformed / reports |
| --- | --- | --- | --- | --- | --- | --- |
| Development | D1 | 6.2% | 2/32 | 30/30 | 0/2 | 0/32 |
| Development | D2 | 6.2% | 2/32 | 30/30 | 0/2 | 0/32 |
| Development | D3 | 6.2% | 2/32 | 30/30 | 0/2 | 0/32 |
| Development | Flat | 6.2% | — | 30/30 | 0/2 | 0/96 |

The flat panel contributes three ballots per trace. A zero denominator means the relevant class was absent.

| Split | Natural traces | J3 fixes | J3 harms | D3 − D2 verdict accuracy (pp) |
| --- | --- | --- | --- | --- |
| Development | 32 | 0 | 0 | +0.00 |

### Paired evidence interventions

| Split | Problem pairs | Whole pair exact | Masked whole pair exact |
| --- | --- | --- | --- |
| dev | 8 | 0.0% | 0.0% |

| Condition | Twin reports | Six fields parsed | Correct solution bit | Correct audit bit | Fault located and repaired / faulty reviews |
| --- | --- | --- | --- | --- | --- |
| visible | 16 | 16 | 16 | 8 | 0/8 |
| masked | 16 | 6 | 6 | 3 | 0/8 |

These evidence measurements use the identical frozen reviewer from alt-exact-j3. They are shared observations.

### Training generation cost

| Role | Calls | Input tokens | Output tokens | CUDA event seconds |
| --- | --- | --- | --- | --- |
| solver | 1024 | 168240 | 6016 | 245.03 |
| j1 | 1024 | 289884 | 6985 | 260.69 |
| j2 | 1024 | 454565 | 13970 | 520.75 |
| j3 | 1024 | 549431 | 13970 | 534.72 |
| development_solver | 64 | 10528 | 345 | 8.64 |

[Machine observations](../../../../results/calibrated/alt-exact-solver)
