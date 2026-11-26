# Running the study

Install uv, Python 3.12 and a CUDA driver compatible with the locked CUDA 13.2 wheel. In this directory run `uv sync --extra gpu`. Copy the environment example to `.env` and set `STUDY_STATE` to a disk with space for trainer snapshots. The local virtual environment is `.venv`. Model files are pinned by revision. [uv PyTorch guide](https://docs.astral.sh/uv/guides/integration/pytorch/) · [PyTorch distributions](https://download.pytorch.org/whl/cu132/torch/)

- `uv run --extra gpu pytest` checks arithmetic, review semantics, problem separation, study design, and statistical pairing.
- `uv run --extra gpu study campaign` schedules all registered runs on one GPU. Rerunning the same command resumes pending work. For a public reproduction, point publication at repositories you control or run the default local campaign. The owning account uses `--publish` to release every milestone.
- `uv run --extra gpu study train --run timing` measures the disposable four-update block. `study train --run d3-17` trains the first solver with the locked budget. `study evaluate --run d3-17` scores the development replay. Final evaluation requires the campaign's completed checkpoint seal.
- `uv run study dashboard` serves the live explorer on the loopback interface. The browser refreshes its observations every 15 seconds. The public Pages explorer reads the last published milestone.
- `uv run study report` regenerates the paper, README score table, progress report, figures, per-experiment notes and website data from raw results.

Model inputs, token chunks and full outputs are printed and saved in timestamped JSONL under `logs`. Raw training and evaluation records live in `results`. Each row includes an expression identity. Training outputs include their assigned reward and independently computed complete-record label. Natural replay keeps all three reports and the three flat ballots on the identical solution. Twin interventions keep observed and expected records in both conditions.

The training runner saves the adapter, optimizer, RNG and Trainer state at group boundaries. Interrupted evaluation resumes by canonical problem ID. Development uses fixed checkpoints and an inspectable split. Final evaluation runs after a digest of every checkpoint is recorded. Any post-registration change belongs in the reviews or amendments with the outcomes visible at the time.
