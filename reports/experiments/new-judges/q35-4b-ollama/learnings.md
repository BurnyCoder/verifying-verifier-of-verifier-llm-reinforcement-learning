# What this run showed

J3 verdict 32/64, twins 1/32, masked 0/32

## A failed evidence pair

Problem `(15 - 6) - 12`. The solver wrote `9,-2`. Judge 1 wrote `0,2,-2`.

| Judge 2 review | Judge 3 wrote | Checker expected |
| --- | --- | --- |
| 0,3,-3,0,2,-3 | 0,2,-2,0,3,-3 | 1,0,-3,0,2,-3 |
| 0,3,-2,0,2,-3 | 0,2,-2,0,2,-3 | 0,3,-3,0,2,-3 |

## A successful evidence pair

Problem `(12 + 12) - 6`. The solver wrote `24,18`. Judge 1 wrote `1,0,18`.

| Judge 2 review | Judge 3 wrote | Checker expected |
| --- | --- | --- |
| 1,0,18,1,0,18 | 1,0,18,1,0,18 | 1,0,18,1,0,18 |
| 1,0,17,1,0,18 | 0,3,18,1,0,18 | 0,3,18,1,0,18 |

[Raw evidence](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/new-judges/q35-4b-ollama).
