# Fresh solver with frozen Judge 3

## Solvers trained with frozen Qwen3.5-4B judges

| Solver reward | Updates | Groups with mixed rewards | Exact development solutions |
| --- | --- | --- | --- |
| Starting solver | 0 | — | 20/32 |
| Frozen Qwen3.5-4B Judge 2 | 256 | 17/256 | 29/32 |
| Frozen Qwen3.5-4B Judge 3 | 0 | — | Scheduled |

The fresh solvers train on the same arithmetic prompts. Each finished checkpoint is scored on the same development questions as the starting solver. [Protocol and decoder](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/blob/main/reports/newer-frozen-judges.md#online-solver-comparison) · [Rollouts, rewards and exact scores](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/new-judges).

No complete training group has been recorded. [Raw solver and judge outputs](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/new-judges/winner-d3)
