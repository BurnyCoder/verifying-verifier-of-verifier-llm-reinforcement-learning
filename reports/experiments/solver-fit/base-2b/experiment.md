# Qwen3.5-2B-Base at NF4

### Solver precision and pretraining-only hardware checks

| Solver | Precision | GPU test | Parsed | Exact | Peak solver allocation |
| --- | --- | --- | --- | --- | --- |
| Qwen3.5-2B-Base | NF4 | One update completed | 16/16 | 12/16 | 3,587 MiB |

Starting accuracy uses greedy decoding on the same train-split calibration problems before the disposable update. The 4B judge ran on the same GPU. Peak allocation is PyTorch memory for the solver process alone. [Hardware protocol](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/blob/main/reports/solver-precision.md) · [Measured costs and outcomes](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/solver-fit).

The four rewards were [1, 0, 1, 1]. The optimizer received mixed rewards and recorded a gradient norm of 6.062. One optimizer step measures hardware feasibility. Establishing a learning effect requires repeated updates and a separate evaluation. [Raw measurements](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/solver-fit/base-2b). [One-step adapter](https://huggingface.co/BurnyCoder/recursive-judge-grpo-adapters/tree/main/runs/solver-fit/base-2b).
