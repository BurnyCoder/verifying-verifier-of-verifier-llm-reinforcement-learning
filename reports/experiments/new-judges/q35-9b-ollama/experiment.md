# Qwen3.5-9B · deployment replicate

Complete. J3 verdict 43/64, twins 1/32, masked 0/32

[Complete raw records](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/new-judges/q35-9b-ollama) · [Case and selection protocol](../../../newer-frozen-judges.md)

| Model and cohort | J1 verdict | J2 verdict | J3 verdict | J3 visible pairs | J3 masked pairs | J3 fixes / new errors |
| --- | --- | --- | --- | --- | --- | --- |
| Qwen3.5-9B · deployment replicate · balanced | 37/64 | 44/64 | 43/64 | 1/32 | 0/32 | 0 / 1 |
| Qwen3.5-9B · deployment replicate · natural | 23/32 | 24/32 | 24/32 | — | — | 0 / 0 |

The release checked 416 scored calls against the original prompts, raw generated text and independent arithmetic values. The masked twins returned identical token sequences on 32/32 pairs. The balanced invalid traces contained 16 first errors before the final step and 16 at the final step. The server recorded 4,110 compute graph assignments across the measured loads. Every assignment used CUDA0.

Windows sampled the dedicated allocation of the llama.cpp process at up to 5,628 MiB. Measured active time between usable adjacent samples was Copy 1.0 s across 73.8 s (13 usable intervals, 0 discarded), 3D 53.6 s across 73.8 s (13 usable intervals, 0 discarded). The sampling window can miss startup and final kernels. Discontinuities supply no time estimate. [Windows timer counters](https://learn.microsoft.com/en-us/windows/win32/wmisdk/timer-algorithm-counter-types).
