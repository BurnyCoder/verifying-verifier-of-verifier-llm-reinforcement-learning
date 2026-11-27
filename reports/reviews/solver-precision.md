# Review of solver precision and pretrained initialization

### Solver precision and pretraining-only hardware checks

| Solver | Precision | GPU test | Parsed | Exact | Peak solver allocation |
| --- | --- | --- | --- | --- | --- |
| Qwen2.5-1.5B-Instruct | NF4 | One update completed | 16/16 | 10/16 | 1,990 MiB |
| Qwen2.5-1.5B-Instruct | BF16 | One update completed | 16/16 | 9/16 | 3,161 MiB |
| Qwen3.5-2B-Base | NF4 | One update completed | 16/16 | 12/16 | 3,587 MiB |

Starting accuracy uses greedy decoding on the same train-split calibration problems before the disposable update. The 4B judge ran on the same GPU. Peak allocation is PyTorch memory for the solver process alone. Against the original NF4 solver, Qwen2.5-1.5B-Instruct at BF16 gained 0 and lost 1 exact answers on the same 16 starting prompts. The descriptive paired difference was -6.2 percentage points (95% resampling interval -18.8 to +0.0). Against the original NF4 solver, Qwen3.5-2B-Base at NF4 gained 4 and lost 2 exact answers on the same 16 starting prompts. The descriptive paired difference was +12.5 percentage points (95% resampling interval -18.8 to +43.8). The pretraining-only base model received rewards [1, 0, 1, 1] and an optimizer gradient norm of 6.062. It is the candidate for a future matched comparison starting before RLVR. The longer-term effect on solver accuracy remains open. [Hardware protocol](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/blob/main/reports/solver-precision.md) · [Measured costs and outcomes](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/solver-fit).

| Trial | Training problem | Solver wrote | Exact | Judge 3 wrote | Reward |
| --- | --- | --- | --- | --- | --- |
| original-nf4 | (7 + 11) + 7 | `18,25` | 1 | `1,0,25,1,0,25` | 1 |
| original-nf4 | (7 + 11) + 7 | `18,25` | 1 | `1,0,25,1,0,25` | 1 |
| original-nf4 | (7 + 11) + 7 | `18,25` | 1 | `1,0,25,1,0,25` | 1 |
| original-nf4 | (7 + 11) + 7 | `18,25` | 1 | `1,0,25,1,0,25` | 1 |
| original-bf16 | (7 + 11) + 7 | `18,25` | 1 | `1,0,25,1,0,25` | 1 |
| original-bf16 | (7 + 11) + 7 | `18,25` | 1 | `1,0,25,1,0,25` | 1 |
| original-bf16 | (7 + 11) + 7 | `18,25` | 1 | `1,0,25,1,0,25` | 1 |
| original-bf16 | (7 + 11) + 7 | `18,25` | 1 | `1,0,25,1,0,25` | 1 |
| base-2b | (7 + 11) + 7 | `18,25` | 1 | `1,0,25,1,0,25` | 1 |
| base-2b | (7 + 11) + 7 | `8,15` | 0 | `0,3,18,0,1,18` | 0 |
| base-2b | (7 + 11) + 7 | `18,25` | 1 | `1,0,25,1,0,25` | 1 |
| base-2b | (7 + 11) + 7 | `11, 18` | 0 | `1,0,18,1,0,18` | 1 |

These training examples follow the starting assessment. A nonzero gradient establishes an update signal on that group. The starting assessment supplies no estimate of post-training accuracy. Published trial adapters and device readings accompany each result. [Source artifacts](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/solver-fit).
