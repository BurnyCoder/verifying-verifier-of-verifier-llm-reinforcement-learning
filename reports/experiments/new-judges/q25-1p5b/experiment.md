# Qwen2.5-1.5B-Instruct · screen

Complete. J3 verdict 28/64, twins 0/32, masked 0/32

[Complete raw records](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/new-judges/q25-1p5b) · [Case and selection protocol](../../../newer-frozen-judges.md)

| Model and cohort | J1 verdict | J2 verdict | J3 verdict | J3 visible pairs | J3 masked pairs | J3 fixes / new errors |
| --- | --- | --- | --- | --- | --- | --- |
| Qwen2.5-1.5B-Instruct · screen · balanced | 32/64 | 28/64 | 28/64 | 0/32 | 0/32 | 16 / 16 |
| Qwen2.5-1.5B-Instruct · screen · natural | 23/32 | 19/32 | 13/32 | — | — | 4 / 10 |

The release checked 416 scored calls against the original prompts, raw generated text and independent arithmetic values. The masked twins returned identical token sequences on 32/32 pairs. The balanced invalid traces contained 16 first errors before the final step and 16 at the final step. The server recorded 2,850 compute graph assignments across the measured loads. Every assignment used CUDA0.

Windows sampled the dedicated allocation of the llama.cpp process at up to 1,262 MiB. At its last sample, per-process engine running time was Copy 0.4 s, 3D 39.2 s. Engine counters include model loading. Sampling can end before the final kernel completes. [Windows GPU accounting](https://devblogs.microsoft.com/directx/gpus-in-the-task-manager/).
