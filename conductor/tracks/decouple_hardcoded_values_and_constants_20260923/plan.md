# Implementation Plan: Decouple Hardcoded Values & Magic Constants across Runtime & Infrastructure

This track eliminates hardcoded project identifiers, Drive folder IDs, magic weeks/dates, user email arrays, and notebook UUIDs across scripts, server, frontend, and deployment automation.

---

## Phase 1: Python Ingestion & CLI Decoupling (`scripts/`)
- [x] Task: Decouple quota and default project resolution in `scripts/gemini_generator.py`, `scripts/pipeline.py`, and `scripts/trigger_sync.py`
  - [x] Replace `"monaro-risk-dev"` fallbacks with dynamic lookup (`os.environ` $\rightarrow$ `gcloud config get-value project`)
  - [x] Add unit test in `tests/test_backend_pipeline.py` verifying dynamic resolution when env vars are unset
- [x] Task: Decouple Drive Folder ID and service account in `scripts/sync_drive.py`
  - [x] Read `folderId` from active project `config.json` (`sources.googleDrive.folderId`) with CLI flag override
  - [x] Construct default deployer service account dynamically using current project ID
  - [x] Add unit test verifying `sync_drive.py` auto-discovers `folderId` from `config.json`
- [x] Task: Phase 1 Verification & Checkpoint
  - [x] Run `uv run pytest tests/test_backend_pipeline.py`

## Phase 2: Dynamic Snapshot & Fallback Resolution (`server.py` & `sync_drive.py`)
- [x] Task: Eliminate magic week strings (`'Week 30'`, `'w27'`, `'Week 27'`)
  - [x] Update `scripts/sync_drive.py:487` to compute `latest_week` dynamically from max week key in `snapshots.json`
  - [x] Update `server.py:353` to resolve the latest snapshot dynamically instead of hardcoding `'w27'`
  - [x] Add unit test verifying snapshot resolution against arbitrary custom week sets
- [x] Task: Phase 2 Verification & Checkpoint
  - [x] Run `uv run pytest tests/test_backend_server.py`

## Phase 3: Frontend Client Decoupling (`src/js/app.js`)
- [x] Task: Decouple hardcoded NotebookLM UUID in `src/js/app.js:3209`
  - [x] Dynamically resolve `notebookDocUrl` from `NOTEBOOK_CATALOG.notebookUrl` or project `config.json`
  - [x] Verify frontend syntax gates via `npm run verify` (`node --check`, ESLint, Vitest)
- [x] Task: Phase 3 Verification & Checkpoint
  - [x] Run `npm run verify` and `uv run pytest tests/test_frontend_integrity.py`

## Phase 4: Environment & Setup Automation Decoupling (`setup.sh`)
- [x] Task: Decouple hardcoded project number `525025654699` in `setup.sh:396`
  - [x] Resolve project number dynamically via `gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)"`
  - [x] Make individual admin user list configurable via `--admins` / `ADMIN_USERS`
- [x] Task: End-to-End Regression Verification & Documentation
  - [x] Run `./setup.sh -l --env dev` read-only health check
  - [x] Run full pytest suite `uv run pytest`
