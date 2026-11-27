# What this run showed

J3 verdict 61/128, twins 1/64, masked 0/64

## A failed evidence pair

Problem `(23 + 1) + 3`. The solver wrote `24,27`. Judge 1 wrote `1,0,27`.

| Judge 2 review | Judge 3 wrote | Checker expected |
| --- | --- | --- |
| 1,0,27,1,0,27 | 0,2,27,0,1,27 | 1,0,27,1,0,27 |
| 1,0,26,1,0,27 | 0,2,27,0,1,27 | 0,3,27,1,0,27 |

## A successful evidence pair

Problem `(28 - 4) - 4`. The solver wrote `24,20`. Judge 1 wrote `1,0,20`.

| Judge 2 review | Judge 3 wrote | Checker expected |
| --- | --- | --- |
| 1,0,20,1,0,20 | 1,0,20,1,0,20 | 1,0,20,1,0,20 |
| 1,0,19,1,0,20 | 0,3,20,1,0,20 | 0,3,20,1,0,20 |

[Raw evidence](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/new-judges/confirm-control).
