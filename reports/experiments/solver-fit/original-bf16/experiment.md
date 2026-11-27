# Qwen2.5-1.5B-Instruct at BF16

### Solver precision and pretraining-only hardware checks

| Solver | Precision | GPU test | Parsed | Exact | Peak solver allocation |
| --- | --- | --- | --- | --- | --- |
| Qwen2.5-1.5B-Instruct | BF16 | One update completed | 16/16 | 9/16 | 3,161 MiB |

Starting accuracy uses greedy decoding on the same train-split calibration problems before the disposable update. The 4B judge ran on the same GPU. Peak allocation is PyTorch memory for the solver process alone. [Hardware protocol](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/blob/main/reports/solver-precision.md) · [Measured costs and outcomes](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/solver-fit).

The four rewards were [1, 1, 1, 1]. The optimizer received equal rewards and recorded a gradient norm of 0. One optimizer step measures hardware feasibility. Establishing a learning effect requires repeated updates and a separate evaluation. [Raw measurements](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/solver-fit/original-bf16). [One-step adapter](https://huggingface.co/BurnyCoder/recursive-judge-grpo-adapters/tree/main/runs/solver-fit/original-bf16).
