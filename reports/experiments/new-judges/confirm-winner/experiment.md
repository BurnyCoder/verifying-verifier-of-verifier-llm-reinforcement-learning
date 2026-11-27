# Qwen3.5-4B · confirmation

Complete. J3 verdict 73/128, twins 10/64, masked 0/64

[Complete raw records](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/new-judges/confirm-winner) · [Case and selection protocol](../../../newer-frozen-judges.md)

| Model and cohort | J1 verdict | J2 verdict | J3 verdict | J3 visible pairs | J3 masked pairs | J3 fixes / new errors |
| --- | --- | --- | --- | --- | --- | --- |
| Qwen3.5-4B · confirmation · balanced | 72/128 | 73/128 | 73/128 | 10/64 | 0/64 | 0 / 0 |

The release checked 640 scored calls against the original prompts, raw generated text and independent arithmetic values. The masked twins returned identical token sequences on 64/64 pairs. The balanced invalid traces contained 32 first errors before the final step and 32 at the final step. The server recorded 6,318 compute graph assignments across the measured loads. Every assignment used CUDA0.

Windows sampled the dedicated allocation of the llama.cpp process at up to 2,872 MiB. Measured active time between usable adjacent samples was Copy 6.1 s across 307.2 s (60 usable intervals, 0 discarded), 3D 179.1 s across 307.2 s (60 usable intervals, 0 discarded). The sampling window can miss startup and final kernels. Discontinuities supply no time estimate. [Windows timer counters](https://learn.microsoft.com/en-us/windows/win32/wmisdk/timer-algorithm-counter-types).
