# Progress · 2026-11-27

23 of 32 registered training blocks have completed. 0 have completed final evaluation. Amended primary comparison is pending. Every arm uses two-add problems and demonstrated prompts.

[Run inventory, including upcoming experiments](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/blob/main/reports/run-inventory.md) · [Newer frozen Qwen protocol](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/blob/main/reports/newer-frozen-judges.md)

Owner prioritized GPU-only frozen newer Qwen judging and deferred optimization and sealed evaluation to a later day. Any conditional solver training with a newer judge is also deferred.

calibrated/top-depth2 · Paused · 20/256 logged, checkpoint 16.

## Newer frozen judges on fixed solver answers

No completed fixed-trace score has been released.

Qwen3.5-9B · Archived, invalid scoring. Empty reasoning wrapper on 65/65 delivered messages. No accuracy estimate..

The matched-depth extension has trained 3 of 4 additional shallow solvers. [Extension](matched-depth-protocol.md).

The timing pilot selected 256 updates per block at 38.3 seconds per pilot update. A block at that rate would take 2.72 hours.

The first single-seed solver has a 14-hour target. The matrix has a one-week training target. Monitoring cadence and milestone order are in the [plan](plan.md). The [experiment index](experiments/experiments.md) contains available development observations.
