---
track_id: gcs_storage_and_config_sync_20260923
type: feature
focus: robustness
status: ACTIVE
bug_id: 104
target_sdd_sections:
  - "2. Data & Storage Layer (Google Drive & GCS Bucket)"
  - "4. Zero-Trust Security, Read-Only Web Tier & Data Isolation"
---
# Specification: GCS-First Storage Architecture & CLI Config Pull/Push Tooling (Delta RFC)

## 1. Overview & Objectives
1. **GCS-First Authoritative Storage (Read & Write across All Generation Pipelines)**: Eliminate local/cloud data divergence (e.g., Week 33 in GCS vs Week 30 on local disk) by ensuring **all generation and ingestion routines**—Executive Summary (`synthesis`, `top3`, `sleeperOutlier`), Podcast Dialogue Transcript (`podcastScript`), and Chirp 3 HD Podcast Audio (`podcast_w*.mp3`)—read and write their outputs directly to **Google Cloud Storage** (`gs://${DATA_BUCKET}/{project}/`).
2. **Mandatory 100% Read-Only Web Tier Invariant**: Enforce `read_only = true` on the Cloud Run Web Service GCS volume mount in Terraform and expose zero web `POST` configuration mutation endpoints, eliminating the web injection attack surface.
3. **Audio & Generation Pipeline Unification**:
   - Remove the legacy `if project == 'monaro': 'assets/...'` exception so all projects persist and reference podcast audio inside `data/<project>/podcast_w*.mp3` (`gs://${DATA_BUCKET}/{project}/podcast_w*.mp3`).
   - Update `check_podcast_status.py` and `ensure_latest_podcast_generated()` (`scripts/sync_drive.py`) to verify `podcast_w*.mp3` existence directly in GCS (`blob_exists_in_gcs`) so local CLI runs don't falsely re-synthesize audio or fail to upload `snapshots.json`.
   - Ensure `ingest_report_file()` (`scripts/pipeline.py`) persists newly generated Executive Summaries, Transcripts, and Audio directly to GCS via `save_json_file()` and `upload_bytes_to_gcs()`.
4. **CLI Config Pull / Edit (`vi`) / Push Workflow (Bug #104)**: Enable operators to pull `config.json` from GCS locally (`--pull-config`), edit it in `vi` (or update specific URLs via `--set-primary-sheet` / `--set-team-google-sheet`), and push/upload it back to GCS (`--push-config` / `--upload-config`) with strict schema and URL validation.

## 2. Proposed Architectural Amendments
- **`deploy/terraform/modules/cloud_run/main.tf` Read-Only Web Mount**: Set `read_only = true` on `google_cloud_run_v2_service.web_service`'s GCS volume mount (`data-volume`), while keeping `read_only = false` strictly on `google_cloud_run_v2_job.sync_job`.
- **`scripts/pipeline.py` & `scripts/sync_drive.py` Generation Persistence to GCS**:
  - **Executive Summary & Transcript (`snapshots.json`)**: Enhancing `load_json_file()` and `save_json_file()` to read and write `<project>/<filename>` directly to `gs://{DATA_BUCKET}/{project}/{filename}` automatically causes `ingest_report_file()` and `ensure_latest_podcast_generated()` to persist generated Executive Summaries (`synthesis`, `top3`, `sleeperOutlier`) and Podcast Transcripts (`podcastScript`) directly into GCS.
  - **Podcast Audio (`podcast_w*.mp3`)**: Removing the `assets/` special case in `pipeline.py`, `sync_drive.py`, and `gemini_generator.py` ensures `synthesize_podcast_audio()` always uploads `podcast_w{week}.mp3` to `gs://{DATA_BUCKET}/{project}/podcast_w{week}.mp3` and sets `snap['audioFile'] = f"data/{project}/podcast_w{week}.mp3"`.
  - **GCS Audio Existence Check**: Add `check_gcs_blob_metadata(bucket_name, blob_name) -> (exists, size_bytes)` so `ensure_latest_podcast_generated()` and `check_podcast_status.py` accurately detect `gs://monaro-risk-dev-data/monaro/podcast_w33.mp3` even when no local copy exists.
- **`scripts/sync_drive.py` Local ADC Impersonation Fallback**: Eagerly refresh impersonated credentials inside `try/except` in `get_drive_service()` so local workstations without `iam.serviceAccounts.getAccessToken` immediately fall back to user ADC credentials.
- **`scripts/security_utils.py` URL & ID Validation**: Add `validate_google_sheet_url()` and `validate_drive_folder_id()` enforcing strict HTTPS Google Workspace domain and ID allowlisting (`docs.google.com/spreadsheets/d/<ID>/edit`, `drive.google.com/.../folders/<ID>`).

## 3. CLI Config Pull / Edit / Push Contracts (`scripts/pipeline.py`)
- **`--pull-config [local_path]`**: Downloads `gs://${DATA_BUCKET}/${project}/config.json` and writes it to `local_path` (defaults to `data/<project>/config.json`) so the operator can open and edit it in `vi` (`vi data/monaro/config.json`).
- **`--push-config [local_path]`** (alias `--upload-config`): Reads the local `config.json` file (defaults to `data/<project>/config.json`), validates JSON structure and all Google Sheet / Drive URLs (`validate_google_sheet_url`, `validate_drive_folder_id`), and uploads it directly to `gs://${DATA_BUCKET}/${project}/config.json`.
- **`--show-config`**: Prints the live `config.json` from GCS to stdout.
- **`--set-primary-sheet <url_or_id>`**, **`--set-team-google-sheet <url_or_id>`**, **`--set-drive-folder <url_or_id>`**: One-liner flags to update specific URLs directly in GCS without manual file editing.

## 4. Acceptance Criteria & Invariants
- All three generation outputs (Executive Summary JSON, Podcast Transcript JSON, and Podcast MP3 Audio) are created and persisted directly in `gs://monaro-risk-dev-data/<project>/` across both Cloud Run Job runs and CLI invocations.
- Local dashboard (`http://localhost:9000/?project=monaro`) reads `snapshots.json`, `config.json`, and `podcast_w33.mp3` directly from `gs://monaro-risk-dev-data/monaro/` and renders Week 33 without manual file copies.
- Cloud Run Web Service mounts the GCS bucket with `read_only = true`, while `#sheetsModal` inputs remain safely `readonly` in the browser.
- Operators can run `--pull-config`, edit `data/monaro/config.json` in `vi`, and run `--push-config` to validate and publish changes to GCS.

## 5. Out of Scope (Deferred to Future Tracks)
- **Live Google Sheets Row Parsing & Schema Mapping**: Full row-level parsing from Google Sheets tabs into `risks.json` and `issues.json` is explicitly decoupled from Bug #104 and deferred to a future track.
