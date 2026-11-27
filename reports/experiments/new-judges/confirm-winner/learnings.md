# What this run showed

J3 verdict 73/128, twins 10/64, masked 0/64

## A failed evidence pair

Problem `(23 + 1) + 3`. The solver wrote `24,27`. Judge 1 wrote `1,0,27`.

| Judge 2 review | Judge 3 wrote | Checker expected |
| --- | --- | --- |
| 1,0,27,1,0,27 | 1,0,27,1,0,27 | 1,0,27,1,0,27 |
| 1,0,26,1,0,27 | 0,2,27,1,0,27 | 0,3,27,1,0,27 |

## A successful evidence pair

Problem `(34 - 4) + 9`. The solver wrote `30,39`. Judge 1 wrote `1,0,39`.

| Judge 2 review | Judge 3 wrote | Checker expected |
| --- | --- | --- |
| 1,0,39,1,0,39 | 1,0,39,1,0,39 | 1,0,39,1,0,39 |
| 1,0,38,1,0,39 | 0,3,39,1,0,39 | 0,3,39,1,0,39 |

[Raw evidence](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/new-judges/confirm-winner).
