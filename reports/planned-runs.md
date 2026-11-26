# Registered run matrix

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
