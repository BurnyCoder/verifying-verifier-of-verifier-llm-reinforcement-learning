# Qwen3.5-4B · deployment replicate

Complete. J3 verdict 32/64, twins 1/32, masked 0/32

[Complete raw records](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/new-judges/q35-4b-ollama) · [Case and selection protocol](../../../newer-frozen-judges.md)

| Model and cohort | J1 verdict | J2 verdict | J3 verdict | J3 visible pairs | J3 masked pairs |
| --- | --- | --- | --- | --- | --- |
| Qwen3.5-4B · deployment replicate · balanced | 32/64 | 32/64 | 32/64 | 1/32 | 0/32 |
| Qwen3.5-4B · deployment replicate · natural | 26/32 | 26/32 | 26/32 | — | — |

The release checked 416 scored calls against the original prompts, raw generated text and independent arithmetic values. The masked twins returned identical token sequences on 32/32 pairs. The balanced invalid traces contained 16 first errors before the final step and 16 at the final step.

Windows sampled the dedicated allocation of the llama.cpp process at up to 2,784 MiB. At its last sample, per-process engine running time was Copy 4.1 s, 3D 1844674407025.2 s. Engine counters include model loading. Sampling can end before the final kernel completes. [Windows GPU accounting](https://devblogs.microsoft.com/directx/gpus-in-the-task-manager/).
