# Fresh solver with frozen Judge 2

## Solvers trained with frozen Qwen3.5-4B judges

| Solver reward | Updates | Groups with mixed rewards | Exact development solutions |
| --- | --- | --- | --- |
| Starting solver | 0 | — | 20/32 (62.5%) |
| Frozen Qwen3.5-4B Judge 1 | 256 | 17/256 | 18/32 (56.2%) |
| Frozen Qwen3.5-4B Judge 2 | 256 | 17/256 | 29/32 (90.6%) |
| Frozen Qwen3.5-4B Judge 3 | 256 | 15/256 | 27/32 (84.4%) |

Relative to the one-judge solver, the two-judge solver gained 12 solutions and lost 1. The three-judge solver gained 10 and lost 1. Three minus two was -6.25 percentage points. The one-judge baseline was registered after the deeper scores were known. On the two-judge run’s own training answers, Judge 2 changed relative credit in 1/256 groups compared with Judge 1. On the three-judge run’s own answers, Judge 3 fixed 4 verdicts and introduced 0 errors, changing relative credit in 0/256 groups. The one- and two-judge runs first sampled different answers at update 8. Their actual relative credit first differed at update 22. The logs leave the cause of the initial divergence unresolved. The paired intervals describe these seed-17 checkpoints on the development cohort. [Protocol and decoder](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/blob/main/reports/newer-frozen-judges.md#online-solver-comparison) · [Rollouts, rewards and exact scores](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/new-judges).

The single-judge arm uses Judge 1's first verdict directly. Each additional judge reads the earlier reports. Only the solver learns. All runs use matched initialization, seed, prompt order and update budget. [One-judge addendum](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/blob/main/reports/newer-frozen-judges.md#one-judge-baseline-addendum).

| Solver comparison | Gained | Lost | Difference (pp) | Paired 95% interval (pp) |
| --- | --- | --- | --- | --- |
| One minus starting solver | 3 | 5 | -6.25 | -25.0 to +9.4 |
| Two minus one | 12 | 1 | +34.38 | +15.6 to +53.1 |
| Three minus one | 10 | 1 | +28.12 | +9.4 to +46.9 |
| Three minus two | 0 | 2 | -6.25 | -15.6 to +0.0 |

Gains and losses compare the same problem across checkpoints. Intervals resample problems within this one seed.

### Grading each checkpoint's fixed answers

| Whose written answers? | Exact solver answers | Correct J1 verdicts | Correct J2 verdicts | Correct J3 verdicts | J3 fixes | J3 new errors |
| --- | --- | --- | --- | --- | --- | --- |
| Solver trained with Judge 1 | 18/32 | 20/32 | 20/32 | 20/32 | 0 | 0 |
| Solver trained with Judge 2 | 29/32 | 28/32 | 28/32 | 28/32 | 0 | 0 |
| Solver trained with Judge 3 | 27/32 | 26/32 | 26/32 | 26/32 | 0 | 0 |

A correct verdict accepts correct arithmetic or rejects an arithmetic or format error. Changing a verdict in this replay leaves the solver’s written answer fixed. All three graders returned the same solution verdict on 96/96 saved development answers across the three checkpoints.

The exact checker accepted 857/1024 training answers. The reward accepted 877/1024, including 117 incorrect answers. It rejected 97 correct answers. 17 of 256 groups supplied mixed rewards. [Raw solver and judge outputs](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/new-judges/winner-d2)
