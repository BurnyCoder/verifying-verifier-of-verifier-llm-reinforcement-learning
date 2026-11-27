# Study summary

## Matched accuracy by judge depth

Each column adds one review of the preceding judge. Judge 1 checks the solver, Judge 2 checks Judge 1, and Judge 3 checks Judge 2. Across a solver-training row only the depth of its reward changes. All solver comparisons here use seed 17.

### Development solver accuracy

Every solver answers the same 32 questions. A solution is correct when every intermediate value is correct. Fitted judges stay frozen during solver updates.

| Training condition | One judge · J1 | Two judges · J2 checks J1 | Three judges · J3 checks J2 |
| --- | --- | --- | --- |
| Only solver trained · original judges | 21/32 (65.6%) | 25/32 (78.1%) | 3/32 (9.4%) |
| Exact-trained judges, then solver | 20/32 (62.5%) | 20/32 (62.5%) | 25/32 (78.1%) |
| Top-down-trained judges, then solver | Pending | Pending | 28/32 (87.5%) |

With judges first trained on exact labels, the one-judge and two-judge solver runs wrote identical text on 1,024/1,024 training completions. Their applied rewards matched on 1,024/1,024, with 1,024 and 1,024 positive rewards respectively. Their solver outputs also matched on 32/32 development questions.

### Development judge verdict accuracy

Every judge grades the same 32 saved responses from the starting solver. A verdict is correct when it agrees with the arithmetic checker. In all judge-only conditions the solver itself stays at 20/32 (62.5%) on the 32 solver-evaluation questions.

| Training condition | One judge · J1 | Two judges · J2 checks J1 | Three judges · J3 checks J2 |
| --- | --- | --- | --- |
| Original frozen judges | 19/32 (59.4%) | 19/32 (59.4%) | 17/32 (53.1%) |
| Exact labels · only final judge trained | 20/32 (62.5%) | 19/32 (59.4%) | 18/32 (56.2%) |
| Exact labels · all participating judges trained | 20/32 (62.5%) | 20/32 (62.5%) | 20/32 (62.5%) |
| Top-down supervision · only final judge trained | 20/32 (62.5%) | 19/32 (59.4%) | 18/32 (56.2%) |
| Top-down supervision · all participating judges trained | 20/32 (62.5%) | 18/32 (56.2%) | 18/32 (56.2%) |

On the original frozen judges’ row, Judge 3 fixed Judge 2’s verdict on 0/32 answers and introduced a grading error on 2/32. Always accepting scores 20/32 (62.5%) on these same responses. The stack trained on exact labels approved all 32 answers at every depth, including all 12 incorrect solutions. The stack trained top-down approved 32, 30, 30 answers at depths one, two and three, respectively. It accepted all 12 incorrect solutions at every depth.

<details><summary>Every verdict Judge 3 changed on the starting solver’s saved answers</summary>

| Problem | Starting solver wrote | Correct steps | Judge 2 | Judge 3 | Effect |
| --- | --- | --- | --- | --- | --- |
| <code>(46 + 3) - 10</code> | <code>56,46</code> | <code>49,39</code> | Endorses Judge 1 and supports the value 46. Rejects the solver and says step 1 should be 46.<br><code>1,0,46,0,1,46</code> | Flags field 3 of Judge 2 and proposes 46. Accepts the solver and gives 46 as its final value.<br><code>0,3,46,1,0,46</code> | Introduced a grading error |
| <code>(1 + 6) - 6</code> | <code>-5,-1</code> | <code>7,1</code> | Invalid review flag -1. Its solver fields say “Accepts the solver and gives -5 as its final value.” The effective verdict is reject.<br><code>-1,-1,-5,1,0,-5</code> | Endorses Judge 2 and supports the value -5. Accepts the solver and gives -5 as its final value.<br><code>1,0,-5,1,0,-5</code> | Introduced a grading error |

</details>

“Only final judge trained” fits the judge used for that column’s terminal decision and uses original judges for preceding calls. “All participating judges trained” uses fitted adapters at every depth. Top-down training uses the shared exact-trained Judge 3. Pending cells have no completed matched measurement. [Matched comparison protocol](matched-depth-protocol.md)

Amended primary comparison is pending. Every arm uses two-add problems and demonstrated prompts.

| Run | Updated role | Updates | Development exact | Development n | Held-out exact | Held-out n |
|---|---|---:|---:|---:|---:|---:|
| base | solver | — | 62.5% | 32 | — | 0 |
| d3-17 | solver | 256 | 9.4% | 32 | — | 0 |
| d2-17 | solver | 256 | 78.1% | 32 | — | 0 |
| d1-17 | solver | 256 | 65.6% | 32 | — | 0 |
| flat-17 | solver | 256 | 75.0% | 32 | — | 0 |
| oracle-17 | solver | 256 | 100.0% | 32 | — | 0 |
| hybrid-17 | solver | 256 | 96.9% | 32 | — | 0 |
| shuffle-17 | solver | 256 | 15.6% | 32 | — | 0 |
| exact-j1 | j1 | 256 | 62.5% | 32 | — | 0 |
| exact-j2 | j2 | 256 | 46.9% | 32 | — | 0 |
| exact-j3 | j3 | 256 | 31.2% | 32 | — | 0 |
| top-j2 | j2 | 256 | 43.8% | 32 | — | 0 |
| top-j1 | j1 | 256 | 50.0% | 32 | — | 0 |
| exact-prefix1 | solver | 256 | 75.0% | 32 | — | 0 |
| exact-prefix2 | solver | 256 | 12.5% | 32 | — | 0 |
| exact-prefix3 | solver | 256 | 78.1% | 32 | — | 0 |
| top-prefix1 | solver | 256 | 6.2% | 32 | — | 0 |
| top-prefix2 | solver | 256 | 96.9% | 32 | — | 0 |
| top-prefix3 | solver | 256 | 87.5% | 32 | — | 0 |
| alt-exact-j1 | j1 | 256 | 62.5% | 32 | — | 0 |
| alt-exact-j2 | j2 | 256 | 46.9% | 32 | — | 0 |
| alt-exact-j3 | j3 | 256 | 31.2% | 32 | — | 0 |
| alt-exact-solver | solver | 256 | 6.2% | 32 | — | 0 |
| alt-top-j3 | j3 | 256 | 31.2% | 32 | — | 0 |
| exact-depth1 | solver | 256 | 62.5% | 32 | — | 0 |
| exact-depth2 | solver | 256 | 62.5% | 32 | — | 0 |
| learn-oracle-17 | solver | 128 | — | 0 | — | 0 |
| learn-shuffle-17 | solver | 128 | — | 0 | — | 0 |

[How the third judge changed actual training rewards and worked examples](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/blob/main/reports/reviews/depth-diagnosis.md). [Side-by-side solver outputs and judge reports](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/blob/main/reports/reviews/paired-outputs-seed-17.md).

**Benchmark difficulty.** The frozen-model screen selected two-add with demonstrated prompts. On 16 screening problems it produced a mix of correct and incorrect answers on 2 problems. [All difficulty levels](learnability.md).

**Solver learning.** Exact-reward training changed complete-trace accuracy on 256 fresh problems by +36.3 percentage points relative to the starting solver (paired 95% interval +30.1 to +42.6). [Shuffled control and arithmetic corrections](learnability.md).

On the original signed development population, base solved 0/32, d3-17 solved 0/32.

**Untrained solver.** Every step was correct on 20 of 32 development problems. Of 0 malformed outputs, 0 contained all correct numbers as named assignments. Judge 3 corrected 0 of Judge 2’s verdicts and introduced 2 errors on these traces.

**First three-judge-trained solver.** Every step was correct on 3 of 32 development problems. Of 1 malformed outputs, 0 contained all correct numbers as named assignments. Judge 3 corrected 1 of Judge 2’s verdicts and introduced 1 errors on these traces.

### Reward and arithmetic during training, seed 17

In the last quarter Judge 3 rewarded **2/15 correct attempts** and **169/241 wrong attempts**. On these identical late answers, Judge 2 would have rewarded 4/15 correct attempts and 176/241 wrong ones. Both grades depend on which answers the evolving solver produces. These trajectories establish when the gap appeared. The contributions of individual updates and seed variation remain distinct questions. [All four quarters, denominators and original records](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/blob/main/reports/reviews/depth-diagnosis.md).

Solver scores require every intermediate value. Judge scores require all fields of the evidence record. Intervals condition on the trained checkpoints. [Preregistration](preregistration.md).
