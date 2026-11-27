# Registered run matrix

The [complete run inventory](run-inventory.md) gives individual optimizer blocks, evaluation-only experiments, archived pilots and scheduled work with their latest measured outcomes. The [frozen Qwen extension](newer-frozen-judges.md) screens three newer deployable configurations against a same-runtime control and specifies a separate confirmation and conditional online comparison.

Each solver row starts from the same untrained solver adapter for its seed except for the explicitly continued alternating block. D1, D2 and D3 denote the terminal judge depth. “Flat” denotes the majority of three separately sampled J1 calls. A judge returning malformed output supplies a negative vote. Every model uses the same base checkpoint, output budget, trace schema and optimizer settings in the [preregistration](preregistration.md).

| Order | Run family | Seeds | Updated role | Reward or evaluation |
|---|---|---|---|---|
| Before training | Base replay | 17 | None | Untrained solver samples, identical traces at D1/D2/D3 and flat voting |
| Timing | Disposable D3 | 17 | Solver | Wall time only determines common update count |
| 1 | D3 | 17 | Solver | Last judge's solution verdict |
| 2 | D2, D1, flat, oracle, hybrid, shuffle | 17 | Fresh solver each | Terminal verdict, majority, full-trace exact bit, D3 × exact bit, or D3 rewards shuffled within a group |
| 3 | Exact J1, J2, J3 | 17 | One judge per block | All fields of the report match the independent checker |
| 4 | Top-down J2, J1 | 17 | One judge per block | Frozen exact J3 approves J2, then frozen top-down J2 approves J1 |
| 5 | Direct and top-down, prefixes 1/2/3 | 17 | Fresh solver each | Three calls throughout, with first one, two or three adapters trained |
| 6 | Alternating direct and top-down | 17 | Three judge blocks and a solver block per route | Refresh train-only examples from that route's solver, update judges, then continue its solver against frozen snapshots |
| 7 | D3, D2, flat replication | 29, 43 | Fresh solver each | Same treatments as the first seed |
| Final | Registered primary and transfer sets | All completed checkpoints | None | Final checkpoint per run, same problem IDs across compared arms |

On the natural replay set report J2→J3 fixes and harms on identical traces. For the evidence intervention, generate twins from the same arithmetic instance and score responses against exact records. Report both the visible and masked conditions. Report actual model tokens, timing, zero-variance groups, malformed outputs and judge/oracle disagreement. Never fill a missing result with an assumed zero.

The [matched-depth extension](matched-depth-protocol.md) adds four fresh shallow solvers with pretrained reviewers and replays the two complete trained judge stacks on fixed starting-solver traces. It reuses the measured three-call solvers and preserves the original primary cohort.

## Learnability amendment

| Phase | Model and trainable roles | Data and budget | Decision |
|---|---|---|---|
| Screen | Same frozen Qwen, no adapters trained | Four arithmetic families, two prompt styles, 16 problems per family, four samples and one greedy trace per problem | Select on solver success, parsing and actual mixed groups |
| Confirm and audit | Frozen solver and frozen J1/J2/J3 | 48 new solver problems, balanced valid/invalid traces and review twins on 16 of them | Confirm learnability range and characterize reward quality |
| Positive and shuffled controls | Separate fresh seed-17 solver adapters | 128 updates per arm, four samples per group, same prompt order | Exact complete-trace reward versus a within-group shuffle of that reward |
| Learning validation | Frozen base and both trained solver checkpoints | Same 256 fresh problems, one greedy completion each | Paired improvement and reward-specificity intervals |
| Matched depth comparison | Repeat all registered solver, judge and alternating arms on fresh role adapters | Freeze the selected family and prompt style. Keep the original per-block update budget and seed schedule. Evaluate 2,048 new problems plus 128 separate review pairs. | Estimate D3 minus D2 on the amended population and report flat voting, signed-difficulty, layout, length and evidence controls |

These are developmental checks ahead of scaling the reward comparison. The first original solver block retains its own name, data, checkpoints and scores. [Decision thresholds](learnability-preregistration.md) · [Measurements](learnability.md)
