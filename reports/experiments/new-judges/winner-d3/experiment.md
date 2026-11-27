# Fresh solver with frozen Judge 3

## Solvers trained with frozen Qwen3.5-4B judges

| Solver reward | Updates | Groups with mixed rewards | Exact development solutions |
| --- | --- | --- | --- |
| Starting solver | 0 | — | 20/32 (62.5%) |
| Frozen Qwen3.5-4B Judge 1 | 256 | 17/256 | 18/32 (56.2%) |
| Frozen Qwen3.5-4B Judge 2 | 256 | 17/256 | 29/32 (90.6%) |
| Frozen Qwen3.5-4B Judge 3 | 256 | 15/256 | 27/32 (84.4%) |

Relative to the one-judge solver, two judges changed development accuracy by +34.38 percentage points and three judges by +28.12. The one-judge baseline was registered after both deeper scores were known. The three-judge solver changed exact development accuracy by -6.25 percentage points relative to the two-judge solver (paired 95% interval -15.6 to +0.0). It gained 0 solutions and lost 2 on the 32 shared problems. During three-judge training, Judge 3 fixed 4 solution verdicts and introduced 0 errors across 1,024 sampled answers. Using Judge 3 changed the within-group advantages in 0/256 groups on those same samples. The interval conditions on these seed-17 checkpoints and the development population. The first difference in sampled solver answers occurred at update 3. All earlier groups gave the two solvers the same relative credit. An earlier change in judge credit therefore cannot explain this first divergence. The logs do not identify which computation produced the differing sample. [Protocol and decoder](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/blob/main/reports/newer-frozen-judges.md#online-solver-comparison) · [Rollouts, rewards and exact scores](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/new-judges).

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

A correct verdict accepts correct arithmetic or rejects an arithmetic or format error. Changing a verdict in this replay leaves the solver’s written answer fixed.

The exact checker accepted 871/1024 training answers. The reward accepted 874/1024, including 106 incorrect answers. It rejected 103 correct answers. 15 of 256 groups supplied mixed rewards. [Raw solver and judge outputs](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/new-judges/winner-d3)
