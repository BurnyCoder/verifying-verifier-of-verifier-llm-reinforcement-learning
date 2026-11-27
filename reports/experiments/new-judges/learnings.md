# Findings on frozen judge releases

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

[All scored runs and costs](experiment.md) · [Protocol](../../newer-frozen-judges.md).
