## Newer frozen judges on fixed solver answers

Every depth grades the same solver responses within a cohort. A visible-pair success requires both complete audit records and the exact numerical correction. Each balanced problem contributes one valid trace and one invalid trace. The last column counts Judge 2 errors that Judge 3 fixed, followed by correct Judge 2 verdicts that Judge 3 overturned.

| Model and cohort | J1 verdict | J2 verdict | J3 verdict | J3 visible pairs | J3 masked pairs | J3 fixes / new errors |
| --- | --- | --- | --- | --- | --- | --- |
| Qwen3.5-9B · deployment replicate · balanced | 37/64 | 44/64 | 43/64 | 1/32 | 0/32 | 0 / 1 |
| Qwen3.5-9B · deployment replicate · natural | 23/32 | 24/32 | 24/32 | — | — | 0 / 0 |
| Qwen3.5-4B · deployment replicate · balanced | 32/64 | 32/64 | 32/64 | 1/32 | 0/32 | 0 / 0 |
| Qwen3.5-4B · deployment replicate · natural | 26/32 | 26/32 | 26/32 | — | — | 0 / 0 |
| Qwen2.5-1.5B-Instruct · screen · balanced | 32/64 | 28/64 | 28/64 | 0/32 | 0/32 | 16 / 16 |
| Qwen2.5-1.5B-Instruct · screen · natural | 23/32 | 19/32 | 13/32 | — | — | 4 / 10 |
| Qwen3.5-4B · screen · balanced | 35/64 | 35/64 | 35/64 | 7/32 | 0/32 | 0 / 0 |
| Qwen3.5-4B · screen · natural | 24/32 | 24/32 | 24/32 | — | — | 0 / 0 |
| Qwen3.5-9B · screen · balanced | 36/64 | 45/64 | 43/64 | 4/32 | 0/32 | 3 / 5 |
| Qwen3.5-9B · screen · natural | 24/32 | 23/32 | 24/32 | — | — | 1 / 0 |
| Qwen3.8-27B · amended screen · balanced | 35/64 | 35/64 | 36/64 | 5/32 | 0/32 | 1 / 0 |
| Qwen3.8-27B · amended screen · natural | 20/32 | 14/32 | 13/32 | — | — | 0 / 1 |
| Qwen2.5-1.5B-Instruct · confirmation · balanced | 64/128 | 63/128 | 61/128 | 1/64 | 0/64 | 23 / 25 |
| Qwen3.5-4B · confirmation · balanced | 72/128 | 73/128 | 73/128 | 10/64 | 0/64 | 0 / 0 |

Qwen3.5-9B · Archived, invalid scoring. Empty reasoning wrapper on 65/65 delivered messages. No accuracy estimate..

Qwen3.5-9B (deployment replicate, Ollama-Qwen3.5-9B-Q4_K_M.gguf) used 191,377 input and 4,963 output tokens in 241.4 seconds of end-to-end calls.

Qwen3.5-4B (deployment replicate, Ollama-Qwen3.5-4B-Q4_K_M.gguf) used 191,363 input and 4,918 output tokens in 158.2 seconds of end-to-end calls.

Qwen2.5-1.5B-Instruct (screen, qwen2.5-1.5b-instruct-q4_k_m.gguf) used 189,653 input and 5,036 output tokens in 61.3 seconds of end-to-end calls.

Qwen3.5-4B (screen, Qwen3.5-4B-Q4_K_M.gguf) used 191,362 input and 4,918 output tokens in 162.2 seconds of end-to-end calls.

Qwen3.5-9B (screen, Qwen3.5-9B-Q4_K_M.gguf) used 191,371 input and 5,018 output tokens in 251.2 seconds of end-to-end calls.

Qwen3.8-27B · Incomplete, sustained latency. The 4 pilot calls averaged 2.56 seconds. Stopped after 51 scored requests. Consecutive requests exceeded the 30-second ceiling and the slowdown persisted after reloading the same file. No cohort accuracy estimate.

Qwen3.8-27B (amended screen, Qwen3.8-27B-UD-IQ1_S.gguf) used 197,374 input and 4,029 output tokens in 866.0 seconds of end-to-end calls.

Qwen2.5-1.5B-Instruct (confirmation, qwen2.5-1.5b-instruct-q4_k_m.gguf) used 298,364 input and 7,883 output tokens in 101.4 seconds of end-to-end calls.

Qwen3.5-4B (confirmation, Qwen3.5-4B-Q4_K_M.gguf) used 301,038 input and 7,660 output tokens in 262.0 seconds of end-to-end calls.

Qwen3.8-27B-UD-IQ2_XS.gguf failed the GPU fit check before generating any answers. The process has 7094.4 MiB in dedicated GPU memory, below 7539.8 MiB of weights and state.

Qwen3.8-27B-UD-IQ2_XXS.gguf failed the GPU fit check before generating any answers. The process has 7034.1 MiB in dedicated GPU memory, below 7139.4 MiB of weights and state.

The comparison of two conversions of the same model was exploratory. Both used the same llama.cpp CUDA executable. The experiment varies each complete model file, so a specific conversion difference cannot be identified as the cause.

Qwen3.5-9B passed 4/32 whole pairs with the Unsloth release and 1/32 with the Ollama release. Of 64 matched visible reviews, 64 had identical messages, 64 had identical rendered prompts, 64 had equal input token counts and 39 produced identical output text.

Qwen3.5-4B passed 7/32 whole pairs with the Unsloth release and 1/32 with the Ollama release. Of 64 matched visible reviews, 64 had identical messages, 64 had identical rendered prompts, 64 had equal input token counts and 27 produced identical output text.

Among the completed original screens, Qwen3.5-4B ranked first. The amended ranking included the completed lower-precision 27B screen.

The screen selected Qwen3.5-4B (Qwen3.5-4B-Q4_K_M.gguf) for independent confirmation against the original frozen model.

Online comparison eligible on a later day.

The candidate-minus-control difference in twins was +14.06 percentage points on 64 paired problems (95% interval +6.25 to +23.44).

The candidate-minus-control difference in balanced verdict was +9.38 percentage points on 64 paired problems (95% interval +1.56 to +17.97).

Intervals resample confirmation problems in pairs and condition on the deployed model files. The solver responses were fixed throughout. Measuring what the solver learns from these rewards requires the deferred online comparison.

[Case identities, selection and interval audit](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/blob/main/reports/reviews/frozen-confirmation.md).

![Frozen verdict and whole-pair accuracy](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/raw/refs/heads/main/docs/assets/frozen-judge-scores.png)

[Protocol and case selection](../../newer-frozen-judges.md).
