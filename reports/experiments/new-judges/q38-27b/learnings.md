# What this run showed

The 4 pilot calls averaged 2.56 seconds. Stopped after 51 scored requests. Consecutive requests exceeded the 30-second ceiling and the slowdown persisted after reloading the same file. No cohort accuracy estimate

Qwen3.8-27B-UD-IQ2_XS.gguf failed the pre-inference GPU check. The process has 7094.4 MiB in dedicated GPU memory, below 7539.8 MiB of weights and state.

Qwen3.8-27B-UD-IQ2_XXS.gguf failed the pre-inference GPU check. The process has 7034.1 MiB in dedicated GPU memory, below 7139.4 MiB of weights and state.

The throughput decision used recorded wall times before and after a reload of the same model. Each row is a completed call.

| Call ID | Completion time (UTC) | Seconds |
| --- | --- | --- |
| natural/f5c50f1e9c2b39262ff407dba817d18d9a739fa3af66af120f8a6723ab175c7f/j2 | 2026-11-27T07:26:41.297+00:00 | 34.2 |
| natural/f5c50f1e9c2b39262ff407dba817d18d9a739fa3af66af120f8a6723ab175c7f/j3 | 2026-11-27T07:29:07.352+00:00 | 146.0 |
| natural/4b6262bff92fb1fc5c27fa64c6847b87db8a3a739f6951b5b38b88992856df45/j1 | 2026-11-27T07:30:31.323+00:00 | 83.9 |
| natural/4b6262bff92fb1fc5c27fa64c6847b87db8a3a739f6951b5b38b88992856df45/j2 | 2026-11-27T07:34:03.325+00:00 | 141.0 |
| natural/4b6262bff92fb1fc5c27fa64c6847b87db8a3a739f6951b5b38b88992856df45/j3 | 2026-11-27T07:36:55.483+00:00 | 172.1 |

[Raw evidence](https://github.com/BurnyCoder/verifying-verifier-of-verifier-llm-reinforcement-learning/tree/main/results/new-judges/q38-27b).
