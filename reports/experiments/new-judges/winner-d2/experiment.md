# Fresh solver with frozen Judge 2

## Solvers trained with frozen Qwen3.5-4B judges

| Solver reward | Updates | Groups with mixed rewards | Exact development solutions |
| --- | --- | --- | --- |
| Starting solver | 0 | — | 20/32 |
| Frozen Qwen3.5-4B Judge 2 | 256 | 17/256 | 29/32 |
| Frozen Qwen3.5-4B Judge 3 | 256 | 15/256 | Trained |

The fresh solvers train on the same arithmetic prompts. Each finished checkpoint is scored on the same development questions as the starting solver. [Protocol and decoder](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/blob/main/reports/newer-frozen-judges.md#online-solver-comparison) · [Rollouts, rewards and exact scores](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/new-judges).

The exact checker accepted 857/1024 training answers. The reward accepted 877/1024, including 117 incorrect answers. It rejected 97 correct answers. 17 of 256 groups supplied mixed rewards. [Raw solver and judge outputs](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/new-judges/winner-d2)
