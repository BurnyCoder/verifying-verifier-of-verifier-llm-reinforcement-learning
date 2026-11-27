# Does a third LLM judge improve GRPO rewards?

A small language model solves numbered arithmetic problems. A second call judges the solution, a third checks that judgment, and a fourth checks the review. An exact integer evaluator can check each answer and each piece of evidence. We measure whether the final reviewer catches errors and whether its reward improves a solver trained with Group Relative Policy Optimization. [Preregistration](reports/preregistration.md)

For example, a solver can give the right final answer to (4 + 3) × 2 while recording 8 in the first step. A reviewer can endorse the correct rejection and still give the wrong correction. The study distinguishes both mistakes.

<!-- RESULTS:START -->
## Why did the two-judge and three-judge solvers diverge?

**With seed 17, training the solver with two frozen judges gave 25/32 correct solutions (78.1%). Training it with three gave 3/32 (9.4%).** The gap was 22 complete solutions (-68.75 percentage points, three minus two). Both solvers started from the same model and saw the same problems in the same order. An integer program graded every intermediate step. On the paired problems, only the two-judge solver was correct on 23, only the three-judge solver on 1, both on 2, and neither on 6. These are development results on the calibrated arithmetic benchmark.

The same evaluation gave 20/32 for the starting solver, 21/32 for one judge, 24/32 for three independent votes, 32/32 for the exact checker, 31/32 for the third judge gated by the exact checker, 5/32 for shuffled three-judge rewards.

### What happens if we stop at Judge 2 on the same answers?

The three-judge-trained solver still solved **3/32**. Its written answers were already fixed before grading. On those answers, Judge 3 changed 2 of Judge 2’s verdicts. It corrected 1 and wrongly overturned 1.

| Stopping point on the fixed answers | Answers approved | Verdicts agreeing with the checker |
| --- | --- | --- |
| Judge 2 | 21/32 | 12/32 |
| Judge 3 | 21/32 | 12/32 |

Every changed development verdict appears here.

| Problem | Submitted steps | Correct steps | Judge 2 | Judge 3 |
| --- | --- | --- | --- | --- |
| (36 - 7) + 7 | 8,15 | 29,36 | Accepted | Rejected |
| (1 + 6) - 6 | -5,-1 | 7,1 | Rejected (invalid audit flag -1) | Accepted |

On `(39 + 12) - 5`, the two-judge-trained solver wrote `51,46`. The three-judge-trained solver wrote `16,11`, and all three judges approved it in the replay.

### What changed during training?

On the same 1,024 training answers sampled by the three-judge solver, Judge 3 fixed 58 of Judge 2’s verdicts and spoiled 44. Substituting Judge 2’s reward would have changed the relative credits in **81/256 optimizer updates**. Each GRPO update compares four answers to one question. When gradings change early on, the solvers can learn different answers and receive different training data at subsequent updates. [GRPO advantage calculation](https://huggingface.co/docs/trl/grpo_trainer#computing-the-advantage)

Judge 3 rewarded **569/880 incorrect answers (64.7%)** and **88/144 correct answers (61.1%)**.

| Within the same training question | Correct answer ranks higher | Tied | Wrong answer ranks higher |
| --- | --- | --- | --- |
| Judge 2 on those answers | 28 | 81 | 25 |
| Judge 3 on those answers | 22 | 84 | 28 |

In its first quarter of training, the three-judge solver produced 80 correct answers per 256 samples and received 173 positive rewards. In the last quarter it produced 15 correct answers and received 171 positive rewards.

The two-judge solver gave the correct first value on 32/32 development problems. The three-judge solver gave a wrong first value on 28 and a malformed answer on 1. In 20 cases it applied the second operation correctly to its own wrong intermediate value. Judge 3 rewarded 357/508 training answers with that error pattern.

### Could a code bug or a training seed explain it?

The audit independently regraded 2,048 training answers and 64 development answers, checked the effective solution-verdict field against each assigned reward, and matched every group mean to TRL’s optimizer log. Prompts and outputs matched the training records for all 7,168 calls, including the solver answer and preceding reports shown to each judge. Both evaluated adapter hashes matched the saved weights. [Transcript and weight checks](results/calibrated/diagnostics/depth-transcripts-17.json)

These checks support a training-signal explanation. The three-judge reward frequently approved incorrect arithmetic and gave little preference to correct answers within a question. The checker-gated control shows that this solver can learn with the same three judge calls when incorrect solutions receive zero reward. The depth analysis is exploratory. The contribution of a particular stochastic update cannot be identified from these trajectories.

### Did Judge 3 actually audit the preceding review?

On a separate replay of the starting solver’s 32 development responses, Judges 1, 2 and 3 agreed with the arithmetic checker on 19, 19 and 17 verdicts, respectively. Three independent first-order votes agreed on 22. On these fixed starting responses Judge 3 repaired 0 earlier verdicts and overturned 2 correct ones.

The paired audit changes a numerical claim in Judge 2’s report while preserving the verdict on the solver. To pass a pair, Judge 3 must endorse the sound report and reject the altered one with the correct location, replacement and solution verdict.

| Judge 3 | Cohort | Correct solver verdict | Altered review located and repaired | Whole pairs correct | Whole pairs with evidence masked |
| --- | --- | --- | --- | --- | --- |
| Frozen | Development | 14/16 | 0/8 | 0/8 | 0/8 |
| Trained on exact labels | Development | 15/16 | 0/8 | 0/8 | 0/8 |
| Alternating, exact route | Development | 16/16 | 0/8 | 0/8 | 0/8 |

A separate experiment keeps **all three judge calls** and varies which reviewers had already been trained before a fresh solver learned. These development scores are exact solver solutions.

| Judge supervision | Only Judge 1 trained | Judges 1 and 2 trained | All three trained |
| --- | --- | --- | --- |
| Exact verdict and evidence | 24/32 | 4/32 | 25/32 |
| Top-down learned supervision | 2/32 | 31/32 | 28/32 |

The preregistered three-seed comparison on 2,048 unseen problems is pending. [Raw training and development audit](reports/reviews/depth-diagnosis.md) · [Preregistration and decision rule](reports/preregistration.md)

## Study results

![Study architecture](docs/assets/architecture.png)

![Learning validation for the exact-reward and shuffled controls](docs/assets/learnability.png)

![Development solver accuracy](docs/assets/outcomes.png)

![Model outputs and exact labels on a common development problem](docs/assets/examples.png)

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
| learn-oracle-17 | solver | 128 | — | 0 | — | 0 |
| learn-shuffle-17 | solver | 128 | — | 0 | — | 0 |

[How the third judge changed actual training rewards and worked examples](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/blob/main/reports/reviews/depth-diagnosis.md).

**Benchmark difficulty.** The frozen-model screen selected two-add with demonstrated prompts. On 16 screening problems it produced a mix of correct and incorrect answers on 2 problems. [All difficulty levels](reports/learnability.md).

**Solver learning.** Exact-reward training changed complete-trace accuracy on 256 fresh problems by +36.3 percentage points relative to the starting solver (paired 95% interval +30.1 to +42.6). [Shuffled control and arithmetic corrections](reports/learnability.md).

On the original signed development population, base solved 0/32, d3-17 solved 0/32.

**Untrained solver.** Every step was correct on 20 of 32 development problems. Of 0 malformed outputs, 0 contained all correct numbers as named assignments. Judge 3 corrected 0 of Judge 2’s verdicts and introduced 2 errors on these traces.

**First three-judge-trained solver.** Every step was correct on 3 of 32 development problems. Of 1 malformed outputs, 0 contained all correct numbers as named assignments. Judge 3 corrected 1 of Judge 2’s verdicts and introduced 1 errors on these traces.

[Interactive results explorer](https://burnycoder.github.io/verifying-verifier-of-verifier-llm-reinforcement-learning/) · [Paper](reports/paper.pdf)
<!-- RESULTS:END -->

### Experiment

The learnability screen measures answer formatting, exact arithmetic and within-problem reward variation on progressively harder tasks. A matched exact-reward and shuffled-reward pilot tests improvement on fresh problems before scaling the study. [Learnability protocol](reports/learnability-preregistration.md)

The first run trains only the solver against three frozen judges. Subsequent runs compare depth, flat voting, programmatic rewards, a hybrid gate and shuffled rewards. We then train the judges one at a time with exact supervision or supervision from the next judge. The final stage trains solvers against partial and complete sets of trained judges and refreshes all four roles in alternating blocks. The primary metric is complete-trace accuracy on the same held-out problems. [Run matrix](reports/planned-runs.md) · [Analysis protocol](reports/preregistration.md)

Prior work established third-order pairwise critique and proof meta-verification. We test an online reward with an executable truth label for each review field. Results apply to this shared-backbone arithmetic system. [Wen et al.](https://arxiv.org/html/2502.04675v4) · [DeepSeekMath-V2](https://arxiv.org/html/2511.22570v1) · [Literature review](reports/literature-review.md) · [State-of-the-art review](reports/state-of-the-art-review.md)

### Reproduction

Use Python 3.12 and uv. The GPU profile uses a CUDA 13.2 PyTorch wheel, a pinned Qwen checkpoint, TRL, PEFT, and bitsandbytes. The CPU profile supports oracle tests, publication and analysis. Copy `.env.example` to `.env` for local storage overrides. Keep credentials in the local GitHub and Hugging Face credential stores. [Qwen model card](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct) · [TRL](https://huggingface.co/docs/trl/grpo_trainer)

```sh
uv sync --extra gpu
uv run --extra gpu pytest
uv run --extra gpu study campaign
uv run study dashboard
uv run study report
```

The campaign measures a disposable block, locks the update budget and completes the original first solver. It then screens the task and measures an exact-reward training gain on fresh problems. A qualifying result fixes the difficulty and prompt style for all matched solver and judge comparisons. Each evaluation links to its checkpoint. The local dashboard reads development measurements as they arrive. The static explorer, figures and paper read persisted results. [Implementation guide](docs/usage.md) · [Study plan](reports/plan.md) · [Progress](reports/progress.md)

### Milestones

- [ ] Complete the frozen-judge solver comparison.
- [ ] Evaluate Judge 3 on natural reviews and paired evidence changes.
- [ ] Compare exact and top-down judge supervision and alternating training.
- [ ] Release complete paired held-out results, positive and negative examples, and the reproducible analysis.
