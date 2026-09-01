# Specification: Scheduled Ingestion Pipeline, Static Sync Architecture & Gemini 2.5 Upgrade

## 1. Overview
This architecture track transitions `project_dash` from a fragile hybrid model—where the frontend attempted to trigger live server-side ETL operations against a static Nginx container—to a robust, decoupled **Scheduled Ingestion Pipeline & Static Sync Architecture (Option B)**.

Additionally, this track updates the AI model configuration from the invalid `gemini-3.5-flash` string to the official **`gemini-2.5-flash`** model across all ingestion and briefing generators, and establishes multiple intuitive triggering mechanisms (Cloud Console 1-click, CLI 1-command, and Cloud Tasks / Cloud Scheduler automation) for developers and administrators.

---

## 2. Architecture & Design Decisions

### 2.1 Decoupled Ingestion Worker (Cloud Run Job)
* **Ingestion Worker**: Data ingestion (Google Drive report scanning, Google Sheets risk synchronization, PDF parsing, and Gemini executive synthesis) is decoupled from the web serving tier and packaged into a standalone Cloud Run Job (`monaro-risk-sync-job`).
* **Web Serving Tier**: Cloud Run web container remains a lightweight, high-performance, and secure static container (`FROM nginx:alpine`) serving pre-rendered HTML, CSS, JavaScript, and static JSON datasets (`data/monaro/snapshots.json`, `data/monaro/config.json`).
* **Zero Secrets on Web Tier**: The web container holds zero credentials, zero service account keys, and zero API tokens. IAM permissions (Drive, Sheets, Vertex AI) exist solely on the Cloud Run Job runtime service account.

### 2.2 Multi-Channel Dev/Admin Triggering
* **Cloud Console (1-Click)**: Developers and administrators can trigger an immediate on-demand synchronization directly in Google Cloud Console:
  * **Via Cloud Run Jobs Console**: Navigate to Cloud Run > Jobs > `monaro-risk-sync-job` > Click **"Execute"**. Real-time logs stream in the console.
  * **Via Cloud Scheduler Console**: Navigate to Cloud Scheduler > `monaro-weekly-sync` > Click **"Force Run"**.
* **CLI (1-Command)**:
  * Native gcloud: `gcloud run jobs execute monaro-risk-sync-job --region=australia-southeast1`
  * Standalone script: `python scripts/trigger_sync.py`
* **Automated Periodic Ingestion**:
  * Cloud Scheduler executes on a weekly/periodic cron schedule, dispatching execution to Cloud Tasks queue (`monaro-sync-queue`) with rate limiting and automatic retry policies.

### 2.3 Frontend Simplification: Read-Only Data Provenance Hub
* **Transform `#sheetsModal`**: The "Workspace Sync" modal is transformed from an interactive ETL form (with non-functional scan/ingest buttons) into an authoritative **Data Provenance & Freshness Hub**:
  * Displays active connected sources (read directly from `config.json`): Joint Sheet link, Team Google Sheet link, Google Drive Folder link, and NotebookLM link.
  * Displays the **Last Synced Timestamp** (from `build_info.json` or `snapshots.json`).
  * Displays the **Latest Ingested Weekly Report** badge (e.g. `✓ Week 30 Ingested`).
  * Displays instructions and deep-links for triggering sync via Cloud Console.
* **Streamlined Freshness Reload (`checkForUpdates`)**:
  * Replace complex `/api/*` fetch functions (`checkDriveSyncStatus`, `ingestReport`, `syncAllWorkspaceSources`) with a single `checkForUpdates()` method that queries `data/${CURRENT_PROJECT}/snapshots.json?t=${Date.now()}` with `cache: 'no-store'`.
  * If new data was deployed via background sync, the dashboard refreshes seamlessly in-place without page reload or backend execution.

### 2.4 Server Simplification (`server.py`)
* **Local Development File Server**: `server.py` is stripped from 638 lines to a lightweight ~50-line static local server with strict no-cache headers.
* **Removal of Legacy API Endpoints**: Remove `/api/check-drive-sync`, `/api/sync-sheet`, `/api/ingest`, `/api/briefing/generate`, and `/api/notebooks` handlers.
* **Elimination of Mock Fallback Arrays**: Permanently remove `DEFAULT_DRIVE_REPORTS` mock lists.

### 2.5 Gemini 2.5 Flash Model Upgrade
* In `scripts/gemini_generator.py` and `scripts/pipeline.py`, update all model definitions from `gemini-3.5-flash` to the official Google model **`gemini-2.5-flash`**.
* Maintain structured JSON output generation using Pydantic schemas (`ExecutiveDecisionBriefing`, `MultispeakerPodcastScript`, `ReportMetadataInspection`).

---

## 3. Functional Requirements

1. **`scripts/sync_drive.py` & Ingestion Engine**:
   - Provide a standalone CLI entrypoint that queries the configured Google Drive folder ID using ADC/Service Account.
   - Detect uningested weekly PDF reports, parse week labels and dates, extract text, call Gemini 2.5 Flash for executive synthesis and podcast scripting, and write updated `snapshots.json`.
   - Update `config.json` with authentic drive report links.

2. **Cloud Run Job Specification (`deploy/Dockerfile.sync`)**:
   - Dockerfile packaging Python 3.13-slim, requirements (`google-genai`, `google-api-python-client`, `pydantic`, `pdfplumber`), and `scripts/`.
   - Entrypoint executes `python scripts/pipeline.py --project=monaro --sync`.

3. **Cloud Tasks & Scheduler Deployment Automation**:
   - Update `deploy/provision_environment.sh` to provision `monaro-risk-sync-job` and Cloud Tasks queue `monaro-sync-queue`.
   - Document Cloud Console 1-click execution in `docs/DEPLOYMENT_GUIDE.md`.

4. **Frontend Provenance Hub & Freshness Check**:
   - Update `index.html` modal structure to clean read-only provenance cards.
   - Update `src/js/app.js` to eliminate dead `/api/*` fetch calls and bind to `checkForUpdates()`.

5. **Local `server.py`**:
   - Serve root directory on port 9000 with `no-store, no-cache, must-revalidate` headers.

---

## 4. Acceptance Criteria
- [ ] Model string across `scripts/gemini_generator.py` and `scripts/pipeline.py` is strictly `gemini-2.5-flash`.
- [ ] No occurrences of `DEFAULT_DRIVE_REPORTS` mock array in `server.py`.
- [ ] `server.py` is under 100 lines of code and serves static assets without error.
- [ ] Workspace Sync modal displays read-only provenance info and live freshness check without firing `/api/*` calls.
- [ ] Dedicated sync script (`scripts/sync_drive.py`) discovers and indexes new Drive files end-to-end.
- [ ] Cloud Run Job configuration is codified and verified in deployment documentation.
- [ ] All existing automated tests in `tests/` pass with 100% success rate under `pytest`.
- [ ] Bug #92 in `.agents/bugs.json` is linked and resolved.

---

## 5. Out of Scope
- Migrating the static frontend from vanilla HTML5/JS to a frontend framework (React/Next.js).
- Modifying the core 5x5 heatmap, driver tree, or ledger calculation logic.
- Building custom Google Workspace add-ons.
