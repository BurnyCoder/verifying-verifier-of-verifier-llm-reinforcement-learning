# Matched comparisons of solver training and judge training

27 November 2026. This extension follows a request to compare one, two, and three judging calls under the same conditions. The first seed's original and calibrated development outcomes, including the direct alternating solver, were already visible. The additional shallow solvers, complete trained-stack replays and sealed test outcomes were unseen when this protocol was written. These comparisons are descriptive. The original three-seed primary decision rule remains in the [preregistration](preregistration.md).

## Solver accuracy

Cross three reward depths with three sources of judges. Use the original frozen Qwen judges, the existing exact-label-trained judge adapters, or the existing top-down-trained judge adapters. A depth-one solver receives Judge 1's solution verdict. Depth two adds Judge 2's review of Judge 1. Depth three adds Judge 3's review of Judge 2. A positive review of a sound rejection gives the solver zero.

Reuse the existing frozen-judge solvers and both fully pretrained depth-three solvers. Train four fresh solvers named `exact-depth1`, `exact-depth2`, `top-depth1` and `top-depth2`. Fix seed 17, the calibrated task and worked examples, solver initialization, example order, group size four, learning rate, optimizer updates, response budgets, stopping rules and greedy evaluation. All fitted judge adapters stay frozen during each solver run. The two routes share the exact-trained Judge 3. Count every intermediate step. Compare the same 32 development and 2,048 sealed problems. Audit the realized training order and seal all four additional checkpoint digests before held-out evaluation.

## Judge accuracy

Hold the starting solver's saved answers fixed, including every space and formatting error. Measure whether the final verdict at each depth agrees with the exact checker. Reuse the same 32 development answers and the same 128 held-out answers used in the registered natural-review replay. Keep the question order, grouping, evaluation seeds and judgment sampling settings identical. The untrained and individually trained judge conditions already have these observations. For each of the two complete trained judge stacks, replay the full chain once and score all three prefixes. A one-call cell can reuse the same Judge 1 checkpoint and the same answers from its isolated evaluation. Record and compare the actual source traces and lower reports.

The individually trained condition changes only the judge at the depth being scored. The complete-stack condition uses fitted adapters for every participating role. Each solver-trained row measures new solutions to common questions. Each judge-trained row measures judgments on identical previously written answers. Keeping the solver frozen fixes its own arithmetic accuracy in every judge-only condition. [Run matrix](planned-runs.md) · [Registered evaluator](../src/study/evaluate.py)
