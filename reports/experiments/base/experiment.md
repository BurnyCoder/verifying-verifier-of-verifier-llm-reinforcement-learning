# base

Role solver. Reward untrained. Seed 17. The fixed architecture, curriculum, optimizer and sample definition are in the [registered protocol](../../preregistration.md).

| Run | Updated role | Updates | Development exact | Development n | Held-out exact | Held-out n |
|---|---|---:|---:|---:|---:|---:|
| base | solver | — | 0.0% | 32 | — | 0 |

### Replaying the same solver outputs

| Split | Rule | Verdict agreement | Exact evidence / traces | False accepts / invalid | False rejects / valid | Malformed / reports |
| --- | --- | --- | --- | --- | --- | --- |
| Development | D1 | 100.0% | 1/32 | 0/32 | 0/0 | 31/32 |
| Development | D2 | 100.0% | 0/32 | 0/32 | 0/0 | 20/32 |
| Development | D3 | 96.9% | 0/32 | 1/32 | 0/0 | 22/32 |
| Development | Flat | 100.0% | — | 0/32 | 0/0 | 87/96 |

The flat panel contributes three ballots per trace. A zero denominator means the relevant class was absent.

| Split | Natural traces | J3 fixes | J3 harms | D3 − D2 verdict accuracy (pp) |
| --- | --- | --- | --- | --- |
| Development | 32 | 0 | 1 | -3.12 |

### Paired evidence interventions

| Split | Problem pairs | Whole pair exact | Masked whole pair exact |
| --- | --- | --- | --- |
| dev | 8 | 0.0% | 0.0% |

[Machine observations](../../../results/base)
