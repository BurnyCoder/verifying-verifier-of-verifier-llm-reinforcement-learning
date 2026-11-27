# Independent review of the Qwen3.5-4B solver-reward comparison

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

| Paired comparison | Problems | Gained | Lost | Difference (pp) | 95% interval (pp) |
| --- | --- | --- | --- | --- | --- |
| Two judges minus starting solver | 32 | 9 | 0 | +28.12 | +12.5 to +43.8 |
| Three judges minus starting solver | 32 | 7 | 0 | +21.88 | +9.4 to +37.5 |
| Three minus two | 32 | 0 | 2 | -6.25 | -15.6 to +0.0 |

The two fresh adapters had the same initial SHA-256 `ab3878076992e76c7a0564c053405ae0463c0809a9e61620cf5c35e96f1954d8`. The actual prompt-order digest for both training trajectories was `172667e238436f39fbea0e9d1aa2b11f6f3b8fea16d6ca3db70fefd916db3051`. The first four sampled answers matched. Both arms produced the same four answers and lower reports on 166 whole groups. Of these, 0 received different group-relative credit. Each effective training reward was recomputed from the raw terminal report and checked against its exact prompt history and the reward mean TRL logged for the optimizer. Every finished checkpoint contributed one greedy trace per development problem. The training and development IDs were disjoint.

## Direct and recursive rewards on the same live answers

| Training run | Verdict comparison | Fixed | Introduced errors | Changed relative credit |
| --- | --- | --- | --- | --- |
| 2 judges | J2 vs J1 | 1 | 0 | 1/256 groups |
| 3 judges | J3 vs J1 | 4 | 0 | 0/256 groups |
| 3 judges | J3 vs J2 | 4 | 0 | 0/256 groups |

Every comparison uses the lower and upper reports from the same training run. A fix or an introduced error counts one answer. A change in relative credit counts one four-answer group. The saved training traces support this substitution without another model call.

| Reward depth | Judge calls | Judge input tokens | Judge output tokens | Training minutes |
| --- | --- | --- | --- | --- |
| 1 | 1,024 | 293,965 | 6,983 | 20.9 |
| 2 | 2,048 | 752,632 | 20,969 | 31.2 |
| 3 | 3,072 | 1,306,285 | 34,985 | 40.0 |

The durations are trainer wall time, including reward generation and periodic probes. [Call timings, GPU engine counters and solver CUDA events](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/new-judges).


### When did training first differ?

The first difference in sampled solver answers occurred at update 3. All earlier groups gave the two solvers the same relative credit. An earlier change in judge credit therefore cannot explain this first divergence. The logs do not identify which computation produced the differing sample.

Both runs received `(50 + 10) - 12` at that update.

| Solver trained with | Sample 1 | Sample 2 | Sample 3 | Sample 4 | Actual rewards |
| --- | --- | --- | --- | --- | --- |
| Judge 2 | `48,36` | `60, 48` | `60,48` | `48,36` | [0, 1, 1, 0] |
| Judge 3 | `48,36` | `60, 48` | `60,48` | `60,48` | [0, 1, 1, 1] |

At update 18, `(20 + 2) - 11` required `22, 11`. Both groups of four received uniform rewards, so every centered advantage was zero.

| Solver wrote | Exact | Judge 2 wrote | J2 reward | Judge 3 wrote | J3 reward |
| --- | --- | --- | --- | --- | --- |
| `21,10` | 0 | `0,1,10,1,0,9` | 1 | `0,3,10,0,1,9` | 0 |
| `21,10` | 0 | `0,1,10,1,0,9` | 1 | `0,3,10,0,1,9` | 0 |
| `21,10` | 0 | `0,1,10,1,0,9` | 1 | `0,3,10,0,1,9` | 0 |
| `21,10` | 0 | `0,1,10,1,0,9` | 1 | `0,3,10,0,1,9` | 0 |

These descriptive examples use the first group in each observed category. Binary rewards are centered within each four-answer group. The fourth field in a parsed higher-order report supplies the solver verdict. [Reward implementation](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/blob/main/src/study/training.py) · [Raw groups](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/new-judges) · [TRL GRPO](https://huggingface.co/docs/trl/grpo_trainer) · [PyTorch reproducibility](https://docs.pytorch.org/docs/stable/notes/randomness.html).

### What each solver wrote on the same calculation

| Expression | Exact steps | One-judge solver | Two-judge solver | Three-judge solver |
| --- | --- | --- | --- | --- |
| (7 - 7) + 12 | 0, 12 | `0,19` (wrong) | `0,19` (wrong) | `0,19` (wrong) |
| (39 + 12) - 5 | 51, 46 | `51,46` (correct) | `51,46` (correct) | `51,46` (correct) |
| (47 - 9) - 7 | 38, 31 | `38, 21` (wrong) | `38,31` (correct) | `38,31` (correct) |
| (12 - 12) + 11 | 0, 11 | `0,13` (wrong) | `0,11` (correct) | `0,13` (wrong) |
| (1 + 6) - 6 | 7, 1 | `7,1` (correct) | `7,-5` (wrong) | `7, -5` (wrong) |

Each row is the first development problem with that combination of successes and failures. The entries give the predicted first and second step. The explorer shows the literal judge reports for every answer in these rows. [Interactive explorer](https://burnycoder.github.io/verifying-verifier-of-verifier-llm-reinforcement-learning/)

