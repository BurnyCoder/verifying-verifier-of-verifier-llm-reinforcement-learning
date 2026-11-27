# Study plan

The [run inventory](run-inventory.md) records each individual treatment and its endpoint. The [newer frozen Qwen experiment](newer-frozen-judges.md) tests fixed responses before allocating solver-training time to a selected judge. The original matched-depth comparison continues through its own sealed evaluation.

Publish the literature reviews, preregistration and run matrix before inference. Publish implementation, tests, protocol paper and website before the first model call. Run the study in the [registered order](planned-runs.md). Use one organization of raw results keyed by run, phase and checkpoint. Keep the final test sealed until model recipes and checkpoints for the comparison are fixed.

Monitor runs lasting 10–30 minutes every five minutes, runs lasting over 30–60 minutes every 15 minutes, and runs over an hour every 30 minutes. Save resumable state and stream the full model I/O. Inspect only development metrics during training. After each training and evaluation milestone, regenerate figures and reports, publish changes and record the checkpoint in one Hugging Face collection.

The final release includes the dated paper, a plain-language summary, a Pages explorer, raw observations, a table of architectures and objectives, per-experiment methods and learnings, and a scientific review. All reported empirical numbers come from machine-readable observations. [Preregistration](preregistration.md) · [Literature](literature-review.md)

The [learnability amendment](learnability-preregistration.md) adds a frozen-model difficulty screen and a true-versus-shuffled exact-reward training check before scaling further comparisons. It preserves the first solver's original recipe and sealed evaluation.
