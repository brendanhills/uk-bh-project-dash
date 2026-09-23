---
track_id: decouple_hardcoded_values_and_constants_20260923
type: refactor
focus: robustness
status: ACTIVE
bug_id: null
target_sdd_sections:
  - "1. Core Architecture & Strict Invariants"
  - "2. Data & Storage Layer (Google Drive & GCS Bucket)"
  - "3. Access Control & Governance (Multi-Tier Architecture)"
  - "5. Turnkey Operations & Handover Tooling"
---

# Specification: Decouple Hardcoded Values & Magic Constants across Runtime & Infrastructure (Delta RFC)

## 1. Overview & Objectives
Eliminate brittle hardcoded constants, fallback project identifiers, drive folders, individual user email addresses, and magic strings across the Python ingestion scripts, backend server, client-side SPA, and deployment automation. Ensure that the codebase dynamically discovers project configuration, credentials, and Workspace source links from environment variables, active `gcloud` settings, and project `config.json` datasets rather than embedding baked-in literals.

## 2. Proposed Architectural Amendments
1. **Dynamic GCP Project & Quota Resolution**:
   - In `scripts/gemini_generator.py`, `scripts/pipeline.py`, and `scripts/trigger_sync.py`, eliminate hardcoded fallback `"monaro-risk-dev"` strings. Resolve dynamically via `os.environ.get("GCP_PROJECT_ID") or os.environ.get("GOOGLE_CLOUD_PROJECT")`, falling back to `gcloud config get-value project` and generic `{prefix}-{env}` prefixes.
2. **Drive Folder & Service Account Dynamic Loading**:
   - In `scripts/sync_drive.py`, eliminate `DEFAULT_DRIVE_FOLDER_ID = '1JIsbi35mXn4W-NxjbLTWo22FQMv_zv-C'`. Load the Drive folder ID directly from `data/<project>/config.json` (`sources.googleDrive.folderId`) or explicit `--folder-id` CLI argument.
   - Construct the default deployer service account dynamically as `github-deployer@{project_id}.iam.gserviceaccount.com`.
3. **Dynamic Snapshot Week Resolution**:
   - In `scripts/sync_drive.py:487` and `server.py:353`, eliminate hardcoded fallback week strings (`'Week 30'`, `'w27'`, `'Week 27'`). Derive the latest reporting week dynamically by inspecting the highest numerical week key in `snapshots.json`.
4. **Decouple Frontend NotebookLM & Report References**:
   - In `src/js/app.js:3209`, replace the hardcoded notebook UUID (`https://notebook.google.com/notebook/acdbb29b-8632...`) with dynamic resolution from `(NOTEBOOK_CATALOG && NOTEBOOK_CATALOG.notebookUrl) || 'https://notebook.google.com'`.
5. **Infrastructure & Script Cleanup**:
   - In `setup.sh:396`, query the GCP project number dynamically via `gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)"` instead of hardcoding `525025654699`.
   - Make individual user admin lists configurable via `--admins` / `ADMIN_USERS` rather than hardcoded email arrays.

## 3. Data Contracts & Interface Changes
- **No breaking API changes**:
  - `server.py` `/api/status`, `/api/sync`, `/api/snapshots` contracts remain identical.
  - CLI commands (`scripts/pipeline.py`, `scripts/sync_drive.py`, `scripts/trigger_sync.py`) retain all existing flags while adding automatic config auto-detection.

## 4. Acceptance Criteria & Invariants
- [ ] 0 hardcoded occurrences of `"monaro-risk-dev"` in `scripts/gemini_generator.py`, `scripts/pipeline.py`, and `scripts/trigger_sync.py`.
- [ ] `scripts/sync_drive.py` resolves `driveFolderId` from `data/<project>/config.json` when `--folder-id` is omitted.
- [ ] Latest snapshot week resolution derives dynamically from snapshot keys with zero hardcoded `'Week 30'` or `'w27'` literals.
- [ ] `src/js/app.js` resolves notebook documentation URLs from project knowledge metadata with zero hardcoded notebook UUIDs.
- [ ] `setup.sh` queries project number dynamically from GCP API rather than hardcoding `525025654699`.
- [ ] 100% automated test pass rate across `pytest` and frontend syntax/lint gates.

## 5. Out of Scope (Deferred to Future Tracks)
- **Common Project Framework Script Overhaul**: Full refactoring of `setup.sh` and `run.sh` into `deploy.sh` and `project_init` standard harnesses is explicitly deferred to Track `common_project_framework_migration_20260923`.
- **Backend On-Demand Podcast API**: Adding interactive backend podcast generation endpoints is explicitly deferred to Track `ondemand_podcast_generation_20260820`.
- **Tailored Stakeholder URL Routing & Views**: URL parameter-driven view slicing (Exec vs. PM vs. Tech) is explicitly deferred to Track `tailored_stakeholder_views`.
