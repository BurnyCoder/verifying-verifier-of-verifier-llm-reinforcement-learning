# What this run showed

J3 verdict 35/64, twins 7/32, masked 0/32

## A failed evidence pair

Problem `(15 - 6) - 12`. The solver wrote `9,-2`. Judge 1 wrote `0,2,-2`.

| Judge 2 review | Judge 3 wrote | Checker expected |
| --- | --- | --- |
| 0,3,-3,0,2,-3 | 0,2,-2,0,2,-2 | 1,0,-3,0,2,-3 |
| 0,3,-2,0,2,-3 | 0,2,-2,0,2,-3 | 0,3,-3,0,2,-3 |

## A successful evidence pair

Problem `(57 + 6) + 12`. The solver wrote `63,75`. Judge 1 wrote `1,0,75`.

| Judge 2 review | Judge 3 wrote | Checker expected |
| --- | --- | --- |
| 1,0,75,1,0,75 | 1,0,75,1,0,75 | 1,0,75,1,0,75 |
| 1,0,74,1,0,75 | 0,3,75,1,0,75 | 0,3,75,1,0,75 |

[Raw evidence](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/new-judges/q35-4b).
