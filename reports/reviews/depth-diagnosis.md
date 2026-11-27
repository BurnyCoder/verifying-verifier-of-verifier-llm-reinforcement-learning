# What changed when the solver trained with a third judge?

This exploratory analysis began after observing the seed-17 development gap. The arithmetic grader executes the numbered operations. The routing check reconstructs the solver verdict from the raw fourth field of each final report and checks each group against TRL’s own optimizer log. A nonbinary audit flag or an unparseable report yields a rejection. [Analysis code](../../src/study/depth_review.py) · [GRPO group advantages](https://huggingface.co/docs/trl/grpo_trainer#computing-the-advantage)

## Seed 17

On 32 matched development problems the two-judge solver alone was correct on 23, the three-judge solver alone on 1, both on 2, and neither on 6. Each row below uses a different trained solver on those same questions. The two graders read identical saved text within each row.

| Final judge used for training | Solutions exactly correct | Judge 2 approved | Judge 3 approved | Grading errors Judge 3 fixed | Grading errors Judge 3 introduced |
| --- | --- | --- | --- | --- | --- |
| Judge 2 | 25/32 | 19/32 | 19/32 | 0 | 0 |
| Judge 3 | 3/32 | 21/32 | 21/32 | 1 | 1 |

[Every paired solver output and all three raw judge reports](paired-outputs-seed-17.md)

| Three-judge solver error | Development answers | Training answers | Training answers rewarded |
| --- | --- | --- | --- |
| correct | 3 | 144 | 88 |
| first wrong, second consistent | 20 | 508 | 357 |
| first wrong, second inconsistent | 8 | 261 | 160 |
| second wrong | 0 | 18 | 3 |
| format | 1 | 93 | 49 |

On the same 1024 training answers, Judge 3 fixed 58 effective Judge 2 verdicts and spoiled 44. Its decision changed the within-group advantages in 81/256 optimizer updates. In 219/256 groups it introduced zero new errors. On 1/256 groups, Judge 2 got every verdict right and Judge 3 both removed credit from a correct answer and paid an incorrect answer. Reward rates below compare all answers of each class on this fixed trajectory.

| Frozen reward source | Correct answers rewarded | Wrong answers rewarded | Correct minus wrong rate (pp) |
| --- | --- | --- | --- |
| Judge 2 | 104/144 (72.2%) | 599/880 (68.1%) | +4.2 |
| Judge 3 | 88/144 (61.1%) | 569/880 (64.7%) | -3.5 |

Within-question pairs compare correct and incorrect completions of the same problem. Pairs within and across rows share observations.

| Reward applied to these answers | Correct ranks higher | Tied | Incorrect ranks higher |
| --- | --- | --- | --- |
| Judge 2 | 28 | 81 | 25 |
| Judge 3 | 22 | 84 | 28 |

| Training run and window | Correct | Rewarded | Sampled |
| --- | --- | --- | --- |
| Two judges / first quarter | 105 | 186 | 256 |
| Two judges / last quarter | 186 | 189 | 256 |
| Three judges / first quarter | 80 | 173 | 256 |
| Three judges / last quarter | 15 | 171 | 256 |

Every development verdict change on the three-judge solver’s fixed responses is shown below.

| Expression | Solver | Exact values | Judge 2 report | Judge 3 report | Verdict change |
| --- | --- | --- | --- | --- | --- |
| (36 - 7) + 7 | 8,15 | 29,36 | 1,0,15,1,0,15 | 1,0,15,0,1,15 | Fixed |
| (1 + 6) - 6 | -5,-1 | 7,1 | -1,-1,-5,1,0,-5 | 1,0,-5,1,0,-5 | Introduced error |

[Two-judge records](../../results/calibrated/d2-17) · [Three-judge records](../../results/calibrated/d3-17)

These comparisons distinguish a change of verdict on an already written answer from a change to the solver learned over successive updates. Replacing the reward in an archived group reveals which relative credits would change on those samples. A separately trained solver generates its own subsequent samples. The checker-gated and shuffled arms test sensitivity to reward quality. The registered effectiveness claim uses unseen problems and multiple training seeds. [Protocol](../preregistration.md) · [All training arms](../summary.md)
