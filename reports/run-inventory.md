# Run inventory

The original solver and judge adapters all use Qwen2.5-1.5B-Instruct. A solver score counts complete arithmetic traces. A trained judge score counts complete evidence records. Stack replays report verdict agreement at each depth on the same saved answers. Pending means the phase has no completed measurement. A dash marks an inapplicable endpoint. Timing and calibration are outside the primary comparison.

### Original signed arithmetic

| Run | Treatment or measurement | Status | Development or pilot result | Held-out result |
| --- | --- | --- | --- | --- |
| [original/base](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/base) | Untrained solver | Archived | 0/32 (0.0%) | Deferred |
| [original/d3-17](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/d3-17) | Fresh solver, frozen J3, seed 17 | Archived | 0/32 (0.0%) | Deferred |
| [original/timing](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/blob/main/results/timing/trained.json) | Disposable solver, frozen J3, wall-clock pilot | Complete | 4 updates in 153.2 s | — |
| original/registered-only | Other original signed treatments and sealed evaluation | Superseded in this campaign | See calibrated arms below | Deferred |

### Difficulty and learning controls

| Run | Treatment or measurement | Status | Development or pilot result | Held-out result |
| --- | --- | --- | --- | --- |
| [screen/one-registered](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/blob/main/results/learnability/screen.json) | Frozen solver, greedy trace | Complete | 0/16 (0.0%) | — |
| [screen/one-demonstrated](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/blob/main/results/learnability/screen.json) | Frozen solver, greedy trace | Complete | 15/16 (93.8%) | — |
| [screen/two-add-registered](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/blob/main/results/learnability/screen.json) | Frozen solver, greedy trace | Complete | 0/16 (0.0%) | — |
| [screen/two-add-demonstrated](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/blob/main/results/learnability/screen.json) | Frozen solver, greedy trace | Complete | 9/16 (56.2%) | — |
| [screen/two-mixed-registered](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/blob/main/results/learnability/screen.json) | Frozen solver, greedy trace | Complete | 0/16 (0.0%) | — |
| [screen/two-mixed-demonstrated](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/blob/main/results/learnability/screen.json) | Frozen solver, greedy trace | Complete | 12/16 (75.0%) | — |
| [screen/registered-registered](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/blob/main/results/learnability/screen.json) | Frozen solver, greedy trace | Complete | 0/16 (0.0%) | — |
| [screen/registered-demonstrated](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/blob/main/results/learnability/screen.json) | Frozen solver, greedy trace | Complete | 2/16 (12.5%) | — |
| [learnability/confirm](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/blob/main/results/learnability/confirm.json) | Fresh difficulty confirmation, greedy trace | Complete | 31/48 (64.6%) | — |
| [learnability/audit](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/blob/main/results/learnability/audit.json) | Frozen balanced verdicts at J1/J2/J3 and visible J3 twins | Complete | 46.9% / 40.6% / 40.6%, twins 0/16 | — |
| [validation/base](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/blob/main/results/learnability/evaluations/base.json) | Frozen solver, independent validation | Complete | 153/256 (59.8%) | — |
| [validation/learn-oracle-17](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/blob/main/results/learnability/evaluations/learn-oracle-17.json) | Solver, exact reward, independent validation | Complete | 246/256 (96.1%) | — |
| [validation/learn-shuffle-17](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/blob/main/results/learnability/evaluations/learn-shuffle-17.json) | Solver, shuffled exact reward, independent validation | Complete | 68/256 (26.6%) | — |

### Main solver and judge study

| Run | Treatment or measurement | Status | Development or pilot result | Held-out result |
| --- | --- | --- | --- | --- |
| [calibrated/base](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/calibrated/base) | Frozen starting solver | Development complete | 20/32 (62.5%) | Deferred |
| [calibrated/d3-17](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/calibrated/d3-17) | Fresh solver, D3, seed 17 | Development complete | 3/32 (9.4%) | Deferred |
| [calibrated/d2-17](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/calibrated/d2-17) | Fresh solver, D2, seed 17 | Development complete | 25/32 (78.1%) | Deferred |
| [calibrated/d1-17](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/calibrated/d1-17) | Fresh solver, D1, seed 17 | Development complete | 21/32 (65.6%) | Deferred |
| [calibrated/flat-17](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/calibrated/flat-17) | Fresh solver, three independent votes, seed 17 | Development complete | 24/32 (75.0%) | Deferred |
| [calibrated/oracle-17](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/calibrated/oracle-17) | Fresh solver, exact trace, seed 17 | Development complete | 32/32 (100.0%) | Deferred |
| [calibrated/hybrid-17](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/calibrated/hybrid-17) | Fresh solver, J3 and checker, seed 17 | Development complete | 31/32 (96.9%) | Deferred |
| [calibrated/shuffle-17](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/calibrated/shuffle-17) | Fresh solver, within-group shuffled J3, seed 17 | Development complete | 5/32 (15.6%) | Deferred |
| [calibrated/exact-j1](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/calibrated/exact-j1) | J1 learns from exact full report | Development complete | 20/32 (62.5%) | Deferred |
| [calibrated/exact-j2](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/calibrated/exact-j2) | J2 learns from exact full report | Development complete | 15/32 (46.9%) | Deferred |
| [calibrated/exact-j3](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/calibrated/exact-j3) | J3 learns from exact full report | Development complete | 10/32 (31.2%) | Deferred |
| [calibrated/top-j2](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/calibrated/top-j2) | J2 learns from exact-j3 | Development complete | 14/32 (43.8%) | Deferred |
| [calibrated/top-j1](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/calibrated/top-j1) | J1 learns from top-j2 | Development complete | 16/32 (50.0%) | Deferred |
| [calibrated/exact-prefix1](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/calibrated/exact-prefix1) | Fresh solver, D3, 1 exact-trained judge, seed 17 | Development complete | 24/32 (75.0%) | Deferred |
| [calibrated/exact-prefix2](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/calibrated/exact-prefix2) | Fresh solver, D3, 2 exact-trained judges, seed 17 | Development complete | 4/32 (12.5%) | Deferred |
| [calibrated/exact-prefix3](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/calibrated/exact-prefix3) | Fresh solver, D3, 3 exact-trained judges, seed 17 | Development complete | 25/32 (78.1%) | Deferred |
| [calibrated/top-prefix1](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/calibrated/top-prefix1) | Fresh solver, D3, 1 top-down judge, seed 17 | Development complete | 2/32 (6.2%) | Deferred |
| [calibrated/top-prefix2](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/calibrated/top-prefix2) | Fresh solver, D3, 2 top-down judges, seed 17 | Development complete | 31/32 (96.9%) | Deferred |
| [calibrated/top-prefix3](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/calibrated/top-prefix3) | Fresh solver, D3, 3 top-down judges, seed 17 | Development complete | 28/32 (87.5%) | Deferred |
| [calibrated/alt-exact-j1](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/calibrated/alt-exact-j1) | J1 learns from exact full report, continuing exact-j1 | Development complete | 20/32 (62.5%) | Deferred |
| [calibrated/alt-exact-j2](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/calibrated/alt-exact-j2) | J2 learns from exact full report, continuing exact-j2 | Development complete | 15/32 (46.9%) | Deferred |
| [calibrated/alt-exact-j3](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/calibrated/alt-exact-j3) | J3 learns from exact full report, continuing exact-j3 | Development complete | 10/32 (31.2%) | Deferred |
| [calibrated/alt-exact-solver](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/calibrated/alt-exact-solver) | Continue solver, D3, 3 exact-trained judges, seed 17 | Development complete | 2/32 (6.2%) | Deferred |
| [calibrated/alt-top-j3](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/calibrated/alt-top-j3) | J3 learns from exact full report, continuing exact-j3 | Development complete | 10/32 (31.2%) | Deferred |
| calibrated/alt-top-j2 | J2 learns from alt-top-j3, continuing top-j2 | Deferred | Pending | Deferred |
| calibrated/alt-top-j1 | J1 learns from alt-top-j2, continuing top-j1 | Deferred | Pending | Deferred |
| calibrated/alt-top-solver | Continue solver, D3, 3 top-down judges, seed 17 | Deferred | Pending | Deferred |
| calibrated/d3-29 | Fresh solver, D3, seed 29 | Deferred | Pending | Deferred |
| calibrated/d2-29 | Fresh solver, D2, seed 29 | Deferred | Pending | Deferred |
| calibrated/flat-29 | Fresh solver, three independent votes, seed 29 | Deferred | Pending | Deferred |
| calibrated/d3-43 | Fresh solver, D3, seed 43 | Deferred | Pending | Deferred |
| calibrated/d2-43 | Fresh solver, D2, seed 43 | Deferred | Pending | Deferred |
| calibrated/flat-43 | Fresh solver, three independent votes, seed 43 | Deferred | Pending | Deferred |

### Matched trained judge depths

| Run | Treatment or measurement | Status | Development or pilot result | Held-out result |
| --- | --- | --- | --- | --- |
| [calibrated/exact-depth1](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/calibrated/exact-depth1) | Fresh solver, D1, 1 exact-trained judge, seed 17 | Development complete | 20/32 (62.5%) | Deferred |
| [calibrated/exact-depth2](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/calibrated/exact-depth2) | Fresh solver, D2, 2 exact-trained judges, seed 17 | Development complete | 20/32 (62.5%) | Deferred |
| [calibrated/top-depth1](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/calibrated/top-depth1) | Fresh solver, D1, 1 top-down judge, seed 17 | Development complete | 25/32 (78.1%) | Deferred |
| calibrated/top-depth2 | Fresh solver, D2, 2 top-down judges, seed 17 | Paused · 20/256 logged, checkpoint 16 | Pending | Deferred |
| [replay/exact](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/calibrated/matched-depth) | Frozen fitted stack, J1/J2/J3 on identical base traces | Development complete | 20/32 · 20/32 · 20/32 | Deferred |
| [replay/top](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/calibrated/matched-depth) | Frozen fitted stack, J1/J2/J3 on identical base traces | Development complete | 20/32 · 18/32 · 18/32 | Deferred |

### Final evaluation and transfer

| Run | Treatment or measurement | Status | Development or pilot result | Held-out result |
| --- | --- | --- | --- | --- |
| analysis/primary | D3 minus D2, paired across seeds 17, 29 and 43 | Deferred | — | Pending |
| analysis/flat | D3 minus three independent votes, same seeds | Deferred | — | Pending |
| cohort/test | Primary arithmetic, 2,048 questions per solver | Deferred | — | Pending |
| cohort/layout | Reserved tree layouts, 128 questions per solver | Deferred | — | Pending |
| cohort/long | Longer expressions, 128 questions per solver | Deferred | — | Pending |
| cohort/original-difficulty | Signed arithmetic, 2,048 questions per solver | Deferred | — | Pending |
| cohort/mechanism | Familiar evidence and layout, 128 evidence pairs, visible and masked | Deferred | — | Pending |
| cohort/unseen-evidence | Unseen error pattern, 128 evidence pairs, visible and masked | Deferred | — | Pending |
| cohort/layout-evidence | Reserved layout, 128 evidence pairs, visible and masked | Deferred | — | Pending |
| cohort/transfer-evidence | Unseen error and reserved layout, 128 evidence pairs, visible and masked | Deferred | — | Pending |

### Newer frozen Qwen judges

| Run | Treatment or measurement | Status | Development or pilot result | Held-out result |
| --- | --- | --- | --- | --- |
| new-judges/q35-9b-ollama | Qwen3.5-9B frozen, Ollama Q4_K_M deployment replicate | Planned | Pending | — |
| new-judges/q35-4b-ollama | Qwen3.5-4B frozen, Ollama Q4_K_M deployment replicate | Planned | Pending | — |
| new-judges/q25-1p5b | Qwen2.5-1.5B-Instruct frozen, same-runtime screen | Planned | Pending | — |
| new-judges/q35-4b | Qwen3.5-4B frozen, same-runtime screen | Planned | Pending | — |
| new-judges/q35-9b | Qwen3.5-9B frozen, same-runtime screen | Planned | Pending | — |
| new-judges/q38-27b | Qwen3.8-27B frozen, same-runtime screen | Planned | Pending | — |
| new-judges/confirm-control | Frozen Qwen2.5 control, fresh confirmation | Conditional | Pending | — |
| new-judges/confirm-winner | Selected newer frozen judge, fresh confirmation | Conditional | Pending | — |
| new-judges/winner-d2 | Fresh Qwen2.5 solver, selected frozen J2 reward, seed 17 | Conditional, later day | Pending | — |
| new-judges/winner-d3 | Fresh Qwen2.5 solver, selected frozen J3 reward, seed 17 | Conditional, later day | Pending | — |

[Run inventory, including upcoming experiments](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/blob/main/reports/run-inventory.md) · [Newer frozen Qwen protocol](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/blob/main/reports/newer-frozen-judges.md)
