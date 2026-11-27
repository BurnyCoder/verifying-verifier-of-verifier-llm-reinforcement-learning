# Qwen2.5-1.5B-Instruct · confirmation

Complete. J3 verdict 61/128, twins 1/64, masked 0/64

[Complete raw records](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/new-judges/confirm-control) · [Case and selection protocol](../../../newer-frozen-judges.md)

| Model and cohort | J1 verdict | J2 verdict | J3 verdict | J3 visible pairs | J3 masked pairs | J3 fixes / new errors |
| --- | --- | --- | --- | --- | --- | --- |
| Qwen2.5-1.5B-Instruct · confirmation · balanced | 64/128 | 63/128 | 61/128 | 1/64 | 0/64 | 23 / 25 |

The release checked 640 scored calls against the original prompts, raw generated text and independent arithmetic values. The masked twins returned identical token sequences on 64/64 pairs. The balanced invalid traces contained 32 first errors before the final step and 32 at the final step. The server recorded 4,386 compute graph assignments across the measured loads. Every assignment used CUDA0.

Windows sampled the dedicated allocation of the llama.cpp process at up to 1,262 MiB. Measured active time between usable adjacent samples was Copy 0.5 s across 139.4 s (26 usable intervals, 0 discarded), 3D 64.4 s across 139.4 s (26 usable intervals, 0 discarded). The sampling window can miss startup and final kernels. Discontinuities supply no time estimate. [Windows timer counters](https://learn.microsoft.com/en-us/windows/win32/wmisdk/timer-algorithm-counter-types).
