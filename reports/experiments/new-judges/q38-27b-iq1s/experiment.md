# Qwen3.8-27B · amended screen

Complete. J3 verdict 36/64, twins 5/32, masked 0/32

[Complete raw records](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/new-judges/q38-27b-iq1s) · [Case and selection protocol](../../../newer-frozen-judges.md)

| Model and cohort | J1 verdict | J2 verdict | J3 verdict | J3 visible pairs | J3 masked pairs | J3 fixes / new errors |
| --- | --- | --- | --- | --- | --- | --- |
| Qwen3.8-27B · amended screen · balanced | 35/64 | 35/64 | 36/64 | 5/32 | 0/32 | 1 / 0 |
| Qwen3.8-27B · amended screen · natural | 20/32 | 14/32 | 13/32 | — | — | 0 / 1 |

The release checked 416 scored calls against the original prompts, raw generated text and independent arithmetic values. The masked twins returned identical token sequences on 32/32 pairs. The balanced invalid traces contained 16 first errors before the final step and 16 at the final step. The server recorded 4,063 compute graph assignments across the measured loads. Every assignment used CUDA0.

Windows sampled the dedicated allocation of the llama.cpp process at up to 6,610 MiB. Measured active time between usable adjacent samples was Copy 11.0 s across 894.9 s (175 usable intervals, 0 discarded), 3D 591.7 s across 879.6 s (172 usable intervals, 3 discarded). The sampling window can miss startup and final kernels. Discontinuities supply no time estimate. [Windows timer counters](https://learn.microsoft.com/en-us/windows/win32/wmisdk/timer-algorithm-counter-types).
