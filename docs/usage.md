# Running the study

Install uv, Python 3.12 and a CUDA driver compatible with the locked CUDA 13.2 wheel. In this directory run `uv sync --extra gpu`. Copy the environment example to `.env` and set `STUDY_STATE` to a disk with space for trainer snapshots. The local virtual environment is `.venv`. Model files are pinned by revision. [uv PyTorch guide](https://docs.astral.sh/uv/guides/integration/pytorch/) · [PyTorch distributions](https://download.pytorch.org/whl/cu132/torch/)

- `uv run --extra gpu pytest` checks arithmetic, review semantics, problem separation, study design, and statistical pairing.
- `uv run --extra gpu study campaign` schedules all registered runs on one GPU. Rerunning the same command resumes pending work. For a public reproduction, point publication at repositories you control or run the default local campaign. The owning account uses `--publish` to release every milestone.
- `uv run --extra gpu study train --run timing` measures the disposable four-update block. `study train --run d3-17` trains the first solver with the locked budget. `study evaluate --run d3-17` scores the development replay. Final evaluation requires the campaign's completed checkpoint seal.
- `uv run study dashboard` serves the live explorer on the loopback interface. The browser refreshes its observations every 15 seconds. The public Pages explorer reads the last published milestone.
- `uv run study report` regenerates the paper, README score table, progress report, figures, per-experiment notes and website data from raw results.

Model inputs, token chunks and full outputs are printed and saved in timestamped JSONL under `logs`. Raw training and evaluation records live in `results`. Each row includes an expression identity. Training outputs include their assigned reward and independently computed complete-record label. Natural replay keeps all three reports and the three flat ballots on the identical solution. Twin interventions keep observed and expected records in both conditions.

The explorer shows every completed optimizer group for the selected run and the latest greedy development probe. Counts under each replay rule distinguish verdict agreement from whole-record evidence accuracy. Generation cost counts non-padding input and output tokens. CUDA-event durations measure elapsed device time around a batched generation call, including gaps between kernels. The pretrained judges share the pinned Qwen backbone. A frozen-adapter checksum with no input tensors means the run loaded no fitted judge adapters.

The training runner saves the adapter, optimizer, RNG and Trainer state at group boundaries. Interrupted evaluation resumes by canonical problem ID. Development uses fixed checkpoints and an inspectable split. Final evaluation runs after a digest of every checkpoint is recorded. Any post-registration change belongs in the reviews or amendments with the outcomes visible at the time.

The seal verifies prompt order and every four-completion group from the raw training observations. Final natural reviews evaluate the same base traces across judge-only arms. Evidence-transfer evaluations cross expression layout with the error in the prior review. When two arms share an identical Judge 3, the evidence cohort records its original source. [Analysis amendments](../reports/amendments.md)

For a fresh replication after cloning a release that already contains observations, set both `STUDY_STATE=.local/replication/checkpoints` and `STUDY_RESULTS=.local/replication/results` in the local environment, then run the ordinary campaign. The report command reads the same paths. Use a distinct pair of directories for another independent replication. Omit these two overrides to regenerate the published tables from the committed observation files.
