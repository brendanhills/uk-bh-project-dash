# Implementation Plan: Scheduled Ingestion Pipeline, Static Sync Architecture & Gemini 2.5 Upgrade

Following the Spec-Driven Development (SDD) and Test-Driven Development (TDD) workflow, all phases require test implementation before code modification, followed by manual/automated verification checkpoints.

---

## Phase 1: Gemini 2.5 Upgrade & Turnkey Ingestion Scripting (TDD First)
Focus: Update AI synthesis to Gemini 2.5 Flash and extract robust, unmocked Google Drive & Sheets synchronization into standalone CLI scripts.

- [ ] Task: Write tests for Gemini 2.5 Flash model configuration and schema validation
  - [ ] Write unit tests in `tests/test_gemini_generator.py` asserting `gemini-2.5-flash` model string resolution
  - [ ] Assert structured JSON extraction for executive briefings and podcast scripts
- [ ] Task: Update model configuration in `scripts/gemini_generator.py` and `scripts/pipeline.py`
  - [ ] Replace `gemini-3.5-flash` with `gemini-2.5-flash` across all generators and CLI defaults
  - [ ] Verify fallback generators and schema validation execute without error
- [ ] Task: Write tests for standalone Drive & Sheets sync engine (`scripts/sync_drive.py`)
  - [ ] Author unit tests in `tests/test_pipeline.py` testing live folder scanning without hardcoded fallbacks
  - [ ] Test incremental snapshot insertion and authentic URL resolution in `data/monaro/snapshots.json`
- [ ] Task: Implement `scripts/sync_drive.py` and unify CLI pipeline
  - [ ] Extract Drive scanning, metadata detection, and snapshot persistence into clean standalone script
  - [ ] Ensure non-zero exit codes and descriptive error reporting upon authentication or folder access failures
- [ ] Task: Phase 1 Verification & Checkpoint (Refer to workflow.md)

---

## Phase 2: Server & Frontend Simplification (Eliminate Ad-hoc REST Handlers)
Focus: Strip `server.py` down to a clean static server and convert the Workspace Sync modal into a clean Read-Only Data Provenance Hub.

- [ ] Task: Write tests for streamlined static `server.py` and static freshness check in `tests/test_server.py`
  - [ ] Test `server.py` serves static assets with strict no-cache headers on port 9000
  - [ ] Assert removal of legacy `/api/check-drive-sync`, `/api/sync-sheet`, and `DEFAULT_DRIVE_REPORTS`
- [ ] Task: Simplify `server.py`
  - [ ] Strip out ~550 lines of ad-hoc HTTP handlers, mock fallbacks, and duplicate logic
  - [ ] Retain clean ~50-line static local development server
- [ ] Task: Write tests for Frontend Provenance Hub and static data reload in `tests/test_presentation.py`
  - [ ] Test `#sheetsModal` renders as a read-only Data Provenance Hub
  - [ ] Test `checkForUpdates()` refreshes static JSON without issuing `/api/*` network requests
- [ ] Task: Refactor `index.html` and `src/js/app.js`
  - [ ] Transform `#sheetsModal` from editable ETL form into Read-Only Provenance Hub with last-sync timestamp and Cloud Console link
  - [ ] Replace fragmented sync functions with single `checkForUpdates()` refreshing static datasets
- [ ] Task: Phase 2 Verification & Checkpoint (Refer to workflow.md)

---

## Phase 3: Cloud Run Job, Cloud Tasks & Cloud Scheduler Infrastructure
Focus: Package the ingestion worker container and configure multi-channel triggering (Cloud Console, CLI, Cloud Tasks).

- [ ] Task: Write tests for Cloud Run Job Dockerfile and provisioning commands in `tests/test_phase6_bugs.py`
  - [ ] Test Cloud Run Job container specification (`deploy/Dockerfile.sync`)
  - [ ] Test Cloud Tasks queue configuration and Cloud Scheduler job parameters
- [ ] Task: Define Ingestion Worker Container & Deployment Configuration
  - [ ] Create `deploy/Dockerfile.sync` packaging Python 3.13-slim and ingestion dependencies
  - [ ] Update `deploy/provision_environment.sh` to provision `monaro-risk-sync-job` and Cloud Tasks queue `monaro-sync-queue`
- [ ] Task: Configure Cloud Tasks, Cloud Scheduler & Cloud Console Quick-Action Runbook
  - [ ] Set up Cloud Scheduler cron to enqueue tasks into Cloud Tasks
  - [ ] Create `scripts/trigger_sync.py` for 1-command CLI dispatch
  - [ ] Document Cloud Console 1-click execution in `docs/DEPLOYMENT_GUIDE.md`
- [ ] Task: Phase 3 Verification & Checkpoint (Refer to workflow.md)

---

## Phase 4: End-to-End Verification & Documentation
Focus: Verify full test suite pass, update documentation, and resolve Bug #92.

- [ ] Task: Run full regression test suite (`pytest`) across all 159+ unit and integration tests
- [ ] Task: Update `docs/DEPLOYMENT_GUIDE.md`, `README.md`, and `tech-stack.md`
- [ ] Task: Update Bug #92 in `.agents/bugs.json` to link to this Conductor track
- [ ] Task: Phase 4 Verification & Checkpoint (Refer to workflow.md)
