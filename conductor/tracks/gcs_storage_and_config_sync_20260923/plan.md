# Implementation Plan: GCS-First Storage Architecture & CLI Config Pull/Push Tooling

## Phase 1: Security Validation & GCS Storage Layer (`scripts/security_utils.py` & `scripts/pipeline.py`)
- [x] Task 1.1: Write unit tests for `validate_google_sheet_url`, `validate_drive_folder_id`, `pull_project_config`, `push_project_config`, `update_project_config`, and GCS-backed `load_json_file` / `save_json_file`.
- [x] Task 1.2: Implement `validate_google_sheet_url` and `validate_drive_folder_id` in `scripts/security_utils.py`.
- [x] Task 1.3: Enhance `load_json_file()` and `save_json_file()` in `scripts/pipeline.py` (plus `check_gcs_blob_metadata()` in `scripts/gemini_generator.py`) to read/write `<project>/<filename>` directly to `gs://{DATA_BUCKET}/{project}/{filename}` so Executive Summary (`synthesis`, `top3`, `sleeperOutlier`) and Podcast Transcript (`podcastScript`) generation in `ingest_report_file()` and `ensure_latest_podcast_generated()` always persist directly to GCS.
- [x] Task 1.4: Update Podcast Audio generation across `scripts/pipeline.py`, `scripts/sync_drive.py`, `scripts/gemini_generator.py`, and `scripts/check_podcast_status.py` to remove the `if project_name == 'monaro': 'assets/...'` special case, ensuring `synthesize_podcast_audio()` always writes `gs://{DATA_BUCKET}/{project}/podcast_w{week}.mp3` (`data/{project}/podcast_w{week}.mp3`) and verifies audio existence in GCS.
- [x] Task 1.5: Implement `--pull-config`, `--push-config` (alias `--upload-config`), `--show-config`, `--set-primary-sheet`, `--set-team-google-sheet`, and `--set-drive-folder` in `scripts/pipeline.py` (and `scripts/sync_drive.py`).

## Phase 2: Read-Only Web Tier Hardening, Drive Auth Fix & Audio Streaming (`main.tf`, `sync_drive.py`, `server.py`)
- [x] Task 2.1: Set `read_only = true` on `google_cloud_run_v2_service.web_service` GCS volume mount in `deploy/terraform/modules/cloud_run/main.tf`.
- [x] Task 2.2: In `scripts/sync_drive.py:get_drive_service()`, call `impersonated.refresh(Request())` inside `try:` so local ADC falls back cleanly to user credentials.
- [x] Task 2.3: Support streaming `/data/<project>/podcast_w*.mp3` (and `/assets/podcast_w*.mp3` fallback) from GCS in `server.py:do_GET()`.
- [x] Task 2.4: In `src/js/app.js:checkForUpdates()`, also refresh `config.json` alongside `snapshots.json` so CLI `--push-config` updates to Sheet URLs appear immediately when clicking "↻ Check for Updates".

## Phase 3: Verification & Checkpoint
- [x] Task 3.1: Run backend (`uv run pytest`) and frontend (`npm run verify`) test suites.
- [~] Task 3.2: User verification of CLI (`--pull-config` -> `vi` -> `--push-config` and `check_podcast_status.py`) and live dashboard (`http://localhost:9000/?project=monaro`).
