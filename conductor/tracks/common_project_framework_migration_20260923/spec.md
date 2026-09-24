---
track_id: common_project_framework_migration_20260923
type: refactor
focus: foundation
status: ACTIVE
bug_id: null
target_sdd_sections:
  - "2.2 Server Runtime & CLI Tooling"
  - "3. Data Architecture & Multi-Project Isolation"
---

# Specification: Migrate to Common Project Framework (`project_init`) (Delta RFC)

## 1. Overview & Objectives
This track migrates `project_dash` (Monaro Risk Intelligence Platform) to achieve **100% `[ALIGNED]` compliance** with the **Standalone Project Environment Standard (`project_init plan`)** while preserving 100% of existing Monaro GCP infrastructure automation (`monaro-risk-dev` / `monaro-risk-prod`), parallel 15-point cloud/Drive health inspection, and `tmux` session management (`run_server.sh`).

Currently:
1. Running `./setup.sh` with no arguments mutates live GCP infrastructure in `monaro-risk-dev` instead of performing safe local developer setup (`uv sync` + `npm install`).
2. `project_init plan` reports 4 gaps (`setup.sh` missing `inspect_status`, missing `./run.sh`, missing `./deploy.sh`, and missing `docs/QUICK_START.md`).
3. Running raw `project_init upgrade` would destructively overwrite the 1,078-line `setup.sh` and drop in generic `run.sh`/`deploy.sh` scripts incompatible with `server.py` (port `9000`), `src/js` ES modules, and `deploy/terraform/`.

## 2. Proposed Architectural Amendments

### 2.1 Promote GCP Provisioning & Cloud State Engine (`setup.sh` -> `deploy.sh`)
- Relocate the 1,078-line Monaro GCP provisioning and parallel 15-check cloud/Drive state inspection engine into `./deploy.sh`.
- Preserve all flags and capabilities in `./deploy.sh`:
  - `--env <dev|prod>` (or positional `dev|prod`), `--project`, `--region`, `--apis-only`, `--folder-id`, `--admin-email`
  - `-l` / `--list` / `--status` (15-point parallel GCP + `gdrive` state inspection)
  - `-m` / `--missing` (missing/unhealthy cloud resource filter)
  - `--state-only` (exact `terraform state list` address format)
  - `--stop` / `--shutdown` / `--pause` (emergency 0%-traffic routing on Cloud Run)
  - `--build` / `build [--env dev|prod]` (direct manual Cloud Build submission via `gcloud builds submit --config=deploy/cloudbuild.yaml`, bypassing GitHub webhook comparison API quirks)
  - Automatic detection and execution of declarative Terraform under `deploy/terraform/environments/${ENV_TARGET}` (`main.tf`) with remote state bucket (`gs://${PROJECT_ID}-terraform-state`).
- Include the `project_init` standard header signature (`./deploy.sh -l, --status`) and fallback guard (`No Cloud Infrastructure Target Configured` if `deploy/terraform` is absent) so `project_init plan` validates `[Harness (deploy)]` as `[ALIGNED]`.

### 2.2 Standardize Local Environment Harness (`./setup.sh` with Cloud Delegation)
- Replace `./setup.sh` with a Common Project Framework-compliant developer harness:
  - **No arguments (`./setup.sh`)**: Safe 1-step local developer onboarding:
    1. Verify `uv`, `gcloud`, `node`, `npm`, and `terraform`.
    2. Scaffold `.env` from `.env.example` if missing.
    3. Sync Python virtual environment (`uv sync`).
    4. Sync Node dependencies (`npm install` when `package.json` is present).
    5. Run fast local health inspection (`inspect_status false`).
  - **Local Status Flags (`./setup.sh -l` / `--status` and `./setup.sh -m` / `--missing`)**:
    - Implements `inspect_status` (satisfying `project_init plan` check `setup.sh -l` + `inspect_status`) checking `tool.gcloud`, `tool.uv`, `tool.node`, `tool.npm`, `tool.terraform`, `python.venv`, `frontend.deps`, `config.env_file`, `config.project_id`, `auth.adc`, required APIs (`aiplatform`, `run`, `cloudbuild`, `storage`), and `script.deploy.sh`.
  - **Backward-Compatible Cloud Delegation**:
    - If `./setup.sh` is invoked with any cloud-specific arguments (`--cloud`, `dev`, `prod`, `--env`, `--state-only`, `--apis-only`, `--stop`, `--shutdown`, `--project`, `--folder-id`), transparently forward execution (`exec ./deploy.sh "$@"`) so existing operator muscle memory (e.g., `./setup.sh -l --env dev` or `./setup.sh --env prod`) works identically without breaking workflows.

### 2.3 Standardize Application Runner (`./run.sh` Integrated with `server.py` & `run_server.sh`)
- Create `./run.sh` adhering to the Common Project Framework contract while tailored to `project_dash`:
  - **Default Port**: `PORT="${PORT:-9000}"` (matching `server.py` and `run_server.sh`).
  - **Standard Flags**:
    - `-l` / `--status`: Sets `RUN_AUDIT_ONLY=true`, runs pre-flight checks (`gcloud`, `uv`, `node`, `ADC_FILE`, `./setup.sh -m`, port `9000` availability), and exits cleanly without starting the server.
    - `-m` / `--missing`: Delegates to `exec ./setup.sh -m`.
    - `-p` / `--port <PORT>`: Overrides `PORT`.
  - **Tmux Lifecycle Forwarding**:
    - When invoked with `start`, `restart`, `stop`, `kill`, `status`, `--no-attach`, or `--tmux`, delegates directly to `exec ./run_server.sh "$@"`.
  - **Frontend JavaScript AST Syntax Pre-Flight Gate (< 15ms)**:
    - Validates `node --check` across `"src/js"` and `"src/js/modules"` (in addition to standard paths) before server startup.
  - **Default Foreground Execution (`./run.sh`)**:
    - Applies Cloudtop SSL/mTLS guardrails (`SSL_CERT_FILE`, `GOOGLE_API_USE_CLIENT_CERTIFICATE=false`, `GOOGLE_API_USE_MTLS_ENDPOINT=never`) and launches `exec env PORT="${PORT}" uv run python server.py`.

### 2.4 Colleague Onboarding Documentation (`docs/QUICK_START.md`)
- Create `docs/QUICK_START.md` documenting 1-step local setup (`./setup.sh`), foreground vs `tmux` execution (`./run.sh` vs `./run_server.sh`), frontend/backend verification (`uv run pytest` and `npm run verify`), and cloud infrastructure auditing (`./deploy.sh -l --env dev`).

## 3. Data Contracts & Interface Changes
- **CLI Entrypoints**:
  - `./setup.sh` -> Local `uv sync` + `npm install` + `inspect_status` (or forwards `--cloud` / `--env dev|prod` to `./deploy.sh`).
  - `./setup.sh -l` / `./setup.sh -m` -> Fast local environment audit (< 2s).
  - `./run.sh` -> Pre-flight gate + `uv run python server.py` on `PORT=9000`.
  - `./run.sh -l` -> Non-blocking pre-flight readiness verification (`RUN_AUDIT_ONLY=true`).
  - `./run.sh start|restart|stop|kill|status|--no-attach` -> Forwards to `./run_server.sh`.
  - `./deploy.sh -l [--env dev|prod]` -> 15-point parallel Monaro GCP & Drive state inspection.
  - `./deploy.sh --env dev|prod` -> Declarative Terraform (`deploy/terraform/environments/{dev,prod}`) + GCP provisioning engine.
- **Automated Test Suite**:
  - Add unit/contract verification ensuring `project_init plan` reports `0 gap(s)` and `setup.sh`, `run.sh`, `deploy.sh`, and `run_server.sh` pass `bash -n` syntax validation and read-only `-l` / `--help` smoke checks.

## 4. Acceptance Criteria & Invariants
1. `project_init plan` exits `0` with **100% `[ALIGNED]`** across all 7 categories (`Package Manager`, `Harness (setup)`, `Harness (run)`, `Harness (deploy)`, `Configuration`, `Documentation`, `VCS Hygiene`).
2. `bash -n setup.sh run.sh deploy.sh run_server.sh` passes with zero errors.
3. `./setup.sh -l` and `./run.sh -l` execute cleanly and exit `0`.
4. `./deploy.sh --help` and `./setup.sh --help` document all local and Monaro cloud options clearly; `./setup.sh -l --env dev` forwards transparently to `./deploy.sh -l --env dev`.
5. Full test suite (`uv run pytest` including `test_frontend_integrity.py` and `npm run verify`) passes 100%.

## 5. Out of Scope (Deferred to Future Tracks)
- **On-Demand Backend Podcast Generation**: Explicitly deferred to pending Track `ondemand_podcast_generation_20260820`.
- **Tailored Stakeholder Views (Exec, PM, and Tech URL-Driven Views)**: Explicitly deferred to pending Track `tailored_stakeholder_views`.
- **Live Cloud Resource Mutation**: Do not apply destructive changes or re-provision live GCP resources in `monaro-risk-dev` or `monaro-risk-prod` during this track; verify strictly via read-only `-l` / `-m` and `project_init plan`.
