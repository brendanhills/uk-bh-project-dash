# Implementation Plan: Migrate to Common Project Framework (`project_init`)

## Phase 1: TDD Contract Test Suite & Cloud Provisioning Migration (`setup.sh` -> `deploy.sh`)
- [ ] Task: Write TDD Harness Contract Tests (`tests/test_harness_contracts.py`)
  - [ ] Add `test_project_init_plan_alignment()` asserting `project_init plan` exits `0` with 0 gaps (`100% aligned`).
  - [ ] Add `test_harness_scripts_bash_syntax()` validating `bash -n` on `setup.sh`, `run.sh`, `deploy.sh`, and `run_server.sh`.
  - [ ] Add `test_setup_and_run_preflight_flags()` verifying `./setup.sh --help`, `./run.sh --help`, `./deploy.sh --help`, `./setup.sh -l`, and `./run.sh -l`.
- [ ] Task: Promote Monaro GCP Provisioning & State Engine into `deploy.sh`
  - [ ] Migrate the 1,078-line Monaro GCP & Drive provisioning engine (`list_environment_state`, `--env dev|prod`, `-l`, `-m`, `--state-only`, `--stop`/`--pause` 0%-traffic shutdown, `deploy/terraform/environments/{dev,prod}` runner, and `gdrive` permission checks) from `setup.sh` into `./deploy.sh`.
  - [ ] Add direct manual Cloud Build submission option (`./deploy.sh --build` / `./deploy.sh build [--env dev|prod]`) invoking `gcloud builds submit --config=deploy/cloudbuild.yaml` to allow immediate zero-webhook manual deployments when GitHub compare API returns 404 (non-fast-forward/rebased history).
  - [ ] Add the `project_init` standard usage signature (`./deploy.sh -l, --status`) and missing-target fallback guard (`No Cloud Infrastructure Target Configured` when `deploy/terraform` is absent) so `project_init plan` marks `[Harness (deploy)]` as `[ALIGNED]`.
  - [ ] Mark `./deploy.sh` executable (`chmod +x`).
- [ ] Task: Phase Verification & Checkpoint (Refer to workflow.md)

## Phase 2: Standardized Local `setup.sh` & `run.sh` Harness Implementation
- [ ] Task: Refactor `setup.sh` to Common Project Framework Local Harness with Cloud Delegation
  - [ ] Implement `inspect_status` (`./setup.sh -l` and `./setup.sh -m`) checking `tool.gcloud`, `tool.uv`, `tool.node`, `tool.npm`, `tool.terraform`, `python.venv`, `frontend.deps`, `config.env_file`, `config.project_id`, `auth.adc`, required APIs, and `script.deploy.sh`.
  - [ ] Configure default no-arg `./setup.sh` to run safe 1-step local developer setup (`ensure_uv`, `ensure_tool`, `.env` from `.env.example`, `uv sync`, `npm install`, `inspect_status false`).
  - [ ] Add transparent argument delegation (`--cloud`, `dev`, `prod`, `--env`, `--state-only`, `--apis-only`, `--stop`, `--shutdown`, `--project`, `--folder-id`) forwarding directly to `exec ./deploy.sh "$@"` to preserve existing operator CLI workflows (`./setup.sh -l --env dev`).
- [ ] Task: Create Standardized `run.sh` Integrated with `server.py` & `run_server.sh`
  - [ ] Implement `./run.sh` with `PORT="${PORT:-9000}"`, `RUN_AUDIT_ONLY` (`-l` / `--status`), `-m` / `--missing`, `-p` / `--port`, `ADC_FILE` check, and Cloudtop SSL/mTLS guardrails.
  - [ ] Configure the Frontend JavaScript AST Syntax Pre-Flight Gate (`node --check`) to validate `"src/js"` and `"src/js/modules"`.
  - [ ] Forward `start | restart | stop | kill | status | --no-attach | --tmux` directly to `exec ./run_server.sh "$@"`, and launch `exec env PORT="${PORT}" uv run python server.py` in default foreground mode.
  - [ ] Mark `./run.sh` executable (`chmod +x`).
- [ ] Task: Phase Verification & Checkpoint (Refer to workflow.md)

## Phase 3: Onboarding Documentation & End-to-End Verification
- [ ] Task: Create `docs/QUICK_START.md` & Update Documentation References
  - [ ] Create `docs/QUICK_START.md` covering 1-step setup (`./setup.sh`), local foreground/tmux execution (`./run.sh` and `./run_server.sh`), frontend/backend verification (`uv run pytest` and `npm run verify`), and cloud state inspection (`./deploy.sh -l --env dev`).
  - [ ] Update `conductor/spec.md` and `conductor/tech-stack.md` CLI tooling references to reflect the separated `setup.sh` / `run.sh` / `deploy.sh` architecture.
- [ ] Task: Run Full Verification Suite
  - [ ] Run `project_init plan` and verify `0 gap(s)` (`100% aligned`).
  - [ ] Run `./setup.sh -l`, `./run.sh -l`, and `uv run pytest` (including `test_harness_contracts.py` and `test_frontend_integrity.py`).
- [ ] Task: Phase Verification & Checkpoint (Refer to workflow.md)
