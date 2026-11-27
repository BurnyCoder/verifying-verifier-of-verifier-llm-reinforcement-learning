# Fresh solver with frozen Judge 2

## Solvers trained with frozen Qwen3.5-4B judges

| Solver reward | Updates | Groups with mixed rewards | Exact development solutions |
| --- | --- | --- | --- |
| Starting solver | 0 | — | 20/32 |
| Frozen Qwen3.5-4B Judge 2 | 256 | 17/256 | 29/32 |
| Frozen Qwen3.5-4B Judge 3 | 256 | 15/256 | 27/32 |

The three-judge solver changed exact development accuracy by -6.25 percentage points relative to the two-judge solver (paired 95% interval -15.6 to +0.0). It gained 0 solutions and lost 2 on the 32 shared problems. During three-judge training, Judge 3 fixed 4 solution verdicts and introduced 0 errors across 1,024 sampled answers. Using Judge 3 changed the within-group advantages in 0/256 groups on those same samples. The interval conditions on these seed-17 checkpoints and the development population. The first difference in sampled solver answers occurred at update 3. All earlier groups gave the two solvers the same relative credit. An earlier change in judge credit therefore cannot explain this first divergence. The logs do not identify which computation produced the differing sample. [Protocol and decoder](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/blob/main/reports/newer-frozen-judges.md#online-solver-comparison) · [Rollouts, rewards and exact scores](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/new-judges).

### Grading each checkpoint's fixed answers

| Whose written answers? | Exact solver answers | Correct J2 verdicts | Correct J3 verdicts | J3 fixes | J3 new errors |
| --- | --- | --- | --- | --- | --- |
| Solver trained with Judge 2 | 29/32 | 28/32 | 28/32 | 0 | 0 |
| Solver trained with Judge 3 | 27/32 | 26/32 | 26/32 | 0 | 0 |

A correct verdict accepts correct arithmetic or rejects an arithmetic or format error. Changing a verdict in this replay leaves the solver’s written answer fixed.

The exact checker accepted 857/1024 training answers. The reward accepted 877/1024, including 117 incorrect answers. It rejected 97 correct answers. 17 of 256 groups supplied mixed rewards. [Raw solver and judge outputs](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/new-judges/winner-d2)
