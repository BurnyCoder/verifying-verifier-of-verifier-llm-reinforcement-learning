# Qwen3.5-2B-Base at NF4

### Solver precision and pretraining-only hardware checks

| Solver | Precision | GPU test | Parsed | Exact | Peak solver allocation |
| --- | --- | --- | --- | --- | --- |
| Qwen3.5-2B-Base | NF4 | One update completed | 16/16 | 12/16 | 3,587 MiB |

Starting accuracy uses greedy decoding on the same train-split calibration problems before the disposable update. The 4B judge ran on the same GPU. Peak allocation is PyTorch memory for the solver process alone. Against the original NF4 solver, Qwen3.5-2B-Base at NF4 gained 4 and lost 2 exact answers on the same 16 starting prompts. The descriptive paired difference was +12.5 percentage points (95% resampling interval -18.8 to +43.8). The pretraining-only base model received rewards [1, 0, 1, 1] and an optimizer gradient norm of 6.062. It is the candidate for a future matched comparison starting before RLVR. The longer-term effect on solver accuracy remains open. [Hardware protocol](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/blob/main/reports/solver-precision.md) · [Measured costs and outcomes](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/solver-fit).

The four rewards were [1, 0, 1, 1]. The optimizer received mixed rewards and recorded a gradient norm of 6.062. One optimizer step measures hardware feasibility. Establishing a learning effect requires repeated updates and a separate evaluation. [Raw measurements](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/solver-fit/base-2b). [One-step adapter](https://huggingface.co/BurnyCoder/recursive-judge-grpo-adapters/tree/main/runs/solver-fit/base-2b).
