# Implementation Plan: Scheduled Ingestion Pipeline & Static Sync Architecture

Following the Implementation-First Velocity and Pragmatic Testing Standards, code is implemented directly with targeted fast-path regression tests and comprehensive end-to-end verification checkpoints.

---

## Phase 1: Gemini 3.7 Upgrade & Turnkey Ingestion Scripting
Focus: Update AI synthesis to Gemini 3.7 Flash and extract robust, unmocked Google Drive & Sheets synchronization into standalone CLI scripts.

- [x] Task: Update model configuration in `scripts/gemini_generator.py`, `scripts/pipeline.py`, and `scripts/sync_drive.py`
  - [x] Configure `gemini-3.7-flash` across all generators and CLI defaults
  - [x] Verify fallback generators and schema validation execute without error
- [x] Task: Implement `scripts/sync_drive.py` and unify CLI pipeline
  - [x] Extract Drive scanning, metadata detection, and snapshot persistence into clean standalone script
  - [x] Ensure non-zero exit codes and descriptive error reporting upon authentication or folder access failures
- [x] Task: Author fast-path regression tests for Gemini 3.7 Flash and sync engine
  - [x] Verify tests in `tests/test_gemini_generator.py`, `tests/test_pipeline.py`, and `tests/test_sync_drive.py`
- [x] Task: Phase 1 Verification & Checkpoint (Refer to workflow.md)

---

## Phase 2: Server & Frontend Simplification (Eliminate Ad-hoc REST Handlers)
Focus: Strip `server.py` down to a clean static server and convert the Workspace Sync modal into a clean Read-Only Data Provenance Hub.

- [x] Task: Simplify `server.py`
  - [x] Eliminate `DEFAULT_DRIVE_REPORTS` hardcoded mock fallback array
  - [x] Delegate Google Drive folder live querying to `scripts.sync_drive`
  - [x] Ensure static development server serves files with strict no-cache headers
- [x] Task: Refactor `index.html` and `src/js/app.js`
  - [x] Transform `#sheetsModal` from editable ETL form into Read-Only Data Provenance Hub with last-sync timestamp and Cloud Console link
  - [x] Replace fragmented `/api/*` sync calls with single client-side static `checkForUpdates()` refreshing snapshots with cache-busting
- [x] Task: Phase 2 Verification & Checkpoint (Refer to workflow.md)

---

## Phase 3: Cloud Run Job, Cloud Tasks & Cloud Scheduler Infrastructure
Focus: Package the ingestion worker container and configure multi-channel triggering (Cloud Console, CLI, Cloud Tasks).

- [x] Task: Define Ingestion Worker Container & Deployment Configuration
  - [x] Create `deploy/Dockerfile.sync` packaging Python 3.13-slim and ingestion dependencies
  - [x] Update `deploy/provision_environment.sh` (Section 7) to provision `monaro-risk-sync-job` and Cloud Tasks queue `monaro-sync-queue`
- [x] Task: Configure Cloud Tasks, Cloud Scheduler & Cloud Console Quick-Action Runbook
  - [x] Create `scripts/trigger_sync.py` for 1-command CLI dispatch (local or cloud)
  - [x] Document Cloud Console 1-click execution and Cloud Tasks in `docs/DEPLOYMENT_GUIDE.md` (Runbook 7)
- [x] Task: Phase 3 Verification & Checkpoint (Refer to workflow.md)

---

## Phase 4: End-to-End Verification & Documentation
Focus: Verify full test suite pass, update documentation, and resolve Bug #92.

- [x] Task: Run full regression test suite (`pytest`) across all 165 unit and integration tests
- [x] Task: Update `docs/DEPLOYMENT_GUIDE.md` and project documentation
- [x] Task: Update Bug #92 in `.agents/bugs.json` to Fix Verified
- [x] Task: Phase 4 Verification & Checkpoint (Refer to workflow.md)
