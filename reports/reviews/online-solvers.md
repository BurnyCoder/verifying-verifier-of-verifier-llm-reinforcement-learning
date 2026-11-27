# Independent review of the Qwen3.5-4B solver-reward comparison

## Solvers trained with frozen Qwen3.5-4B judges

| Solver reward | Updates | Groups with mixed rewards | Exact development solutions |
| --- | --- | --- | --- |
| Starting solver | 0 | — | 20/32 (62.5%) |
| Frozen Qwen3.5-4B Judge 1 | 256 | 17/256 | Trained |
| Frozen Qwen3.5-4B Judge 2 | 256 | 17/256 | 29/32 (90.6%) |
| Frozen Qwen3.5-4B Judge 3 | 256 | 15/256 | 27/32 (84.4%) |

The three-judge solver changed exact development accuracy by -6.25 percentage points relative to the two-judge solver (paired 95% interval -15.6 to +0.0). It gained 0 solutions and lost 2 on the 32 shared problems. During three-judge training, Judge 3 fixed 4 solution verdicts and introduced 0 errors across 1,024 sampled answers. Using Judge 3 changed the within-group advantages in 0/256 groups on those same samples. The interval conditions on these seed-17 checkpoints and the development population. The first difference in sampled solver answers occurred at update 3. All earlier groups gave the two solvers the same relative credit. An earlier change in judge credit therefore cannot explain this first divergence. The logs do not identify which computation produced the differing sample. [Protocol and decoder](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/blob/main/reports/newer-frozen-judges.md#online-solver-comparison) · [Rollouts, rewards and exact scores](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/new-judges).

The single-judge arm uses Judge 1's first verdict directly. Each additional judge reads the earlier reports. Only the solver learns. All runs use matched initialization, seed, prompt order and update budget. [One-judge addendum](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/blob/main/reports/newer-frozen-judges.md#one-judge-baseline-addendum).

### Grading each checkpoint's fixed answers

| Whose written answers? | Exact solver answers | Correct J2 verdicts | Correct J3 verdicts | J3 fixes | J3 new errors |
| --- | --- | --- | --- | --- | --- |
| Solver trained with Judge 2 | 29/32 | 28/32 | 28/32 | 0 | 0 |
| Solver trained with Judge 3 | 27/32 | 26/32 | 26/32 | 0 | 0 |

A correct verdict accepts correct arithmetic or rejects an arithmetic or format error. Changing a verdict in this replay leaves the solver’s written answer fixed.

| Paired comparison | Problems | Gained | Lost | Difference (pp) | 95% interval (pp) |
| --- | --- | --- | --- | --- | --- |
| Two judges minus starting solver | 32 | 9 | 0 | +28.12 | +12.5 to +43.8 |
| Three judges minus starting solver | 32 | 7 | 0 | +21.88 | +9.4 to +37.5 |
| Three minus two | 32 | 0 | 2 | -6.25 | -15.6 to +0.0 |

The two fresh adapters had the same initial SHA-256 `ab3878076992e76c7a0564c053405ae0463c0809a9e61620cf5c35e96f1954d8`. The actual prompt-order digest for both training trajectories was `172667e238436f39fbea0e9d1aa2b11f6f3b8fea16d6ca3db70fefd916db3051`. The first four sampled answers matched. Both arms produced the same four answers and lower reports on 166 whole groups. Of these, 0 received different group-relative credit. Each effective training reward was recomputed from the raw terminal report and checked against its exact prompt history and the reward mean TRL logged for the optimizer. Every finished checkpoint contributed one greedy trace per development problem. The training and development IDs were disjoint.

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

### Both solvers on the same development calculation

| Expression | Exact steps | Two-judge-trained solver and reviews | Three-judge-trained solver and reviews |
| --- | --- | --- | --- |
| (12 - 12) + 11 | 0, 11 | `0,11` (correct), J2 `1,0,11,1,0,11`, J3 `1,0,11,1,0,11` | `0,13` (wrong), J2 `1,0,13,1,0,13`, J3 `1,0,13,1,0,13` |
| (39 + 12) - 5 | 51, 46 | `51,46` (correct), J2 `1,0,46,1,0,46`, J3 `1,0,46,1,0,46` | `51,46` (correct), J2 `1,0,46,1,0,46`, J3 `1,0,46,1,0,46` |
| (7 - 7) + 12 | 0, 12 | `0,19` (wrong), J2 `1,0,19,1,0,19`, J3 `1,0,19,1,0,19` | `0,19` (wrong), J2 `1,0,19,1,0,19`, J3 `1,0,19,1,0,19` |

Each solver writes its answer before grading. In the six-number reviews, the first number audits the preceding judge and the fourth accepts or rejects the solver. The examples take the first problem in each observed pair of outcomes in evaluation order.

