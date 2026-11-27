# Running the study

Install uv, Python 3.12 and a CUDA driver compatible with the locked CUDA 13.2 wheel. In this directory run `uv sync --extra gpu`. Copy the environment example to `.env` and set `STUDY_STATE` to a disk with space for trainer snapshots. The local virtual environment is `.venv`. Model files are pinned by revision. [uv PyTorch guide](https://docs.astral.sh/uv/guides/integration/pytorch/) · [PyTorch distributions](https://download.pytorch.org/whl/cu132/torch/)

- `uv run --extra gpu pytest` checks arithmetic, review semantics, problem separation, study design, and statistical pairing.
- `uv run --extra gpu study campaign` schedules all registered runs on one GPU. Rerunning the same command resumes pending work. For a public reproduction, point publication at repositories you control or run the default local campaign. The owning account uses `--publish` to release every milestone.
- `uv run --extra gpu study train --run timing` measures the disposable four-update block. `study train --run d3-17` trains the first solver with the locked budget. `study evaluate --run d3-17` scores the development replay. Final evaluation requires the campaign's completed checkpoint seal.
- `uv run study dashboard` serves the live explorer on the loopback interface. The browser refreshes its observations every 15 seconds. The public Pages explorer reads the last published milestone.
- `uv run study report` regenerates the paper, README score table, progress report, figures, per-experiment notes and website data from raw results.

The README’s depth diagnosis regrades training and development records each time the report builds. With the full local journals and saved adapters, `uv run python -m study.depth_transcripts --seed 17` also verifies each generated prompt, response and checkpoint hash. The compact verification receipts travel with the published results. [Depth diagnosis](../reports/reviews/depth-diagnosis.md)

After the final campaign completion receipt exists, the same report command regenerates `reports/reviews/final.md`. It re-executes every primary and transfer solution, checks natural and evidence-altered reviews, tests the observed training and development IDs against the reserved populations, verifies the seal, and tabulates matched gains and losses for each depth comparison. [Final review implementation](../src/study/final_review.py)

The calibrated campaign automatically runs the four additional matched-depth solvers and two fixed-answer judge-stack replays. In a calibrated environment, individual examples of the same entry points are `uv run study train --run exact-depth2` and `uv run study stack-replay --route exact`. The held-out extension requires both the original and additional checkpoint seals. [Matched-depth protocol](../reports/matched-depth-protocol.md)

Model inputs, token chunks and full outputs are printed and saved in timestamped JSONL under `logs`. Raw training and evaluation records live in `results`. Each row includes an expression identity. Training outputs include their assigned reward and independently computed complete-record label. Natural replay keeps all three reports and the three flat ballots on the identical solution. Twin interventions keep observed and expected records in both conditions.

The explorer shows every completed optimizer group for the selected run and the latest greedy development probe. Counts under each replay rule distinguish verdict agreement from whole-record evidence accuracy. Generation cost counts non-padding input and output tokens. CUDA-event durations measure elapsed device time around a batched generation call, including gaps between kernels. The pretrained judges share the pinned Qwen backbone. A frozen-adapter checksum with no input tensors means the run loaded no fitted judge adapters.

The training runner saves the adapter, optimizer, RNG and Trainer state at group boundaries. Interrupted evaluation resumes by canonical problem ID. Development uses fixed checkpoints and an inspectable split. Final evaluation runs after a digest of every checkpoint is recorded. Any post-registration change belongs in the reviews or amendments with the outcomes visible at the time.

The seal verifies prompt order and every four-completion group from the raw training observations. Final natural reviews evaluate the same base traces across judge-only arms. Evidence-transfer evaluations cross expression layout with the error in the prior review. When two arms share an identical Judge 3, the evidence cohort records its original source. [Analysis amendments](../reports/amendments.md)

The campaign writes scheduled checks to each run's `monitor.jsonl`, the terminal and `reports/progress.md`. It uses measured throughput to estimate remaining training time. Checks on ongoing final evaluations disclose only completed record counts. A worker exit wakes the supervisor immediately.

For a fresh replication after cloning a release that already contains observations, set both `STUDY_STATE=.local/replication/checkpoints` and `STUDY_RESULTS=.local/replication/results` in the local environment, then run the ordinary campaign. The report command reads the same paths. Use a distinct pair of directories for another independent replication. Omit these two overrides to regenerate the published tables from the committed observation files.

The learnability experiment runs via `uv run --extra gpu study learnability campaign`. It screens problem difficulty and prompt style on the frozen model, confirms the chosen setting, audits the three frozen judges, and trains matched exact-reward and shuffled-reward solvers. Each phase resumes from raw observations or an optimizer checkpoint. The owning account adds `--publish` to update the public repositories at every milestone. [Selection rules](../reports/learnability-preregistration.md) · [Measured learnability](../reports/learnability.md)

The default campaign retains the original frozen-judge solver, runs the learnability experiment and starts the matched matrix when its registered learning criterion is met. Its frozen decision and source digests are in `results/calibrated/profile.json`. All amended raw results, role adapters and logs are in their own `calibrated` subdirectories. The final seal covers that matrix alone. The amended benchmark uses new problem IDs, with a second cohort for judging evidence and signed harder expressions for transfer. To reproduce the entire original design independently, use `study campaign --registered-only` with a fresh pair of result and state directories. The normal `study report` detects the frozen decision and includes observations from the initial study.

## Using a published adapter

The model repository stores each original adapter in `runs/RUN_ID` and each amended adapter in `runs/calibrated/RUN_ID`. Download a released directory and load its adapter on the pinned base model. The `timing` directory contains the disposable timing-policy adapter. The study runtime loads the base with the registered NF4 configuration in `src/study/backend.py`. [Released adapters](https://huggingface.co/BurnyCoder/recursive-judge-grpo-adapters/tree/main/runs) · [PEFT checkpoint format](https://huggingface.co/docs/peft/developer_guides/checkpoint)

```sh
hf download BurnyCoder/recursive-judge-grpo-adapters --include 'runs/timing/*' --local-dir .local/release
```

```python
from peft import PeftModel
from transformers import AutoModelForCausalLM

base = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen2.5-1.5B-Instruct",
    revision="989aa7980e4cf806f80c7fef2b1adb7bc71aa306",
    dtype="auto",
)
policy = PeftModel.from_pretrained(base, ".local/release/runs/timing").eval()
```
## GPU-only frozen-judge experiment

Install the project's uv environment and a CUDA build of llama.cpp b12807. Set `STUDY_LLAMA_SERVER` to the path to its server executable and `STUDY_FROZEN_DIR` to a directory with room for the pinned GGUF artifacts. On Windows the release contains a server archive and a matching CUDA runtime archive. Extract both into the same directory. Check `llama-server --list-devices` for CUDA0. [Pinned release](https://github.com/ggml-org/llama.cpp/releases/tag/b12807) · [Registered weights and checksums](../src/study/frozen_models.py)

```powershell
uv sync --extra gpu
$env:STUDY_TRACK = "calibrated"
uv run study frozen-judges
uv run study report
```

The command downloads and checks each artifact, verifies full GPU placement, runs fixed-answer and evidence-twin probes, and confirms the selected judge on independent development IDs. Restart the same command after interruption. It checks prompt and configuration identity before reusing completed calls. Keep the archived calibrated base replay under `results/calibrated/base/`. Use the default local mode for independent replications. The research repository owner uses `--publish` to release every completed milestone. All optimizer work remains deferred. [Study protocol](../reports/newer-frozen-judges.md)

On Windows the device sampler records the llama.cpp process's dedicated and shared allocations and cumulative GPU engine running time. Each recorded native graph assignment is checked against CUDA0 when releasing the results. The Hugging Face dataset contains compressed server and prompt logs. These counters and the separate prompt-processing and decoding durations measure different parts of execution. [Windows GPU accounting](https://devblogs.microsoft.com/directx/gpus-in-the-task-manager/) · [Raw public archive](https://huggingface.co/datasets/BurnyCoder/recursive-judge-grpo-study)
