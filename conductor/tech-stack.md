# Tech Stack Definition: Monaro Risk Intelligence Platform

## 1. Core Architecture & Strict Invariants
- **Automated Cloud Run Deployment with IAP Google SSO:**
  - Automated CI/CD deployment via **Google Cloud Build** triggers on push to `dev` (scoped to `project_dash/**`).
  - Containerized deployment to **Google Cloud Run** secured behind **Identity-Aware Proxy (IAP)** with `--no-allow-unauthenticated`.
  - Seamless corporate Google SSO authorization tied to Google Groups (`monaro-risk-dev@google.com` / `monaro-risk-prod@google.com`).
- **Frontend Architecture:** High-performance, decoupled Single Page Application (`index.html`) using modern JavaScript ES6+, Tailwind CSS, and Chart.js.
- **Runtime Model:** Lightweight containerized Python/Nginx server (`server.py`) serving the client-side SPA, project data files, and on-demand sync APIs.
- **Local / Cloudtop Runner:** Local Python 3.11+ server managed via 1-command tmux lifecycle (`run_server.sh`) on port 9000 for development and review.

## 2. Data & Storage Layer (Google Drive & GCS Bucket)
- **Authoritative Storage Directive (GCS-First):** All runtime project datasets (`snapshots.json`, `config.json`, `risks.json`, `issues.json`) and rendered podcast audio binaries (`data/<project>/podcast_w*.mp3`) MUST be stored authoritatively in **Google Cloud Storage** (`gs://${DATA_BUCKET}/{project}/`, e.g. `gs://monaro-risk-dev-data/monaro/`). Do not rely on local `DATA_DIR` folder overrides or offline local copies; both Cloud Run (via `/app/data` GCS volume mount) and local development servers (`server.py` / `scripts/pipeline.py` via `DATA_BUCKET`) read and write directly to the target GCS bucket.
- **Mandatory 100% Read-Only Web Tier Invariant:** The Cloud Run Web Presentation Service (`monaro-risk-dash-dev` / `monaro-risk-dash-prod`) MUST mount the GCS data bucket strictly as **Read-Only (`read_only = true`)** and expose **zero web `POST` configuration mutation endpoints**. Only the scheduled/background ingestion job (`monaro-risk-sync-job`) and authorized developer/operator CLI commands (`scripts/pipeline.py`) authenticated via GCP IAM (`roles/storage.objectAdmin`) may write to GCS.
- **Primary Source of Truth:** Google Drive Shared Folder / Workspace Storage.
- **Podcast Audio & Snapshot Persistence:** Rendered audio binaries (`.mp3`) and snapshot registries are persisted directly to Google Cloud Storage (`gs://${DATA_BUCKET}/{project}/`) via Cloud Run volume mounts (`/app/data`) and direct GCS bucket I/O.
- **Weekly Ingestion Pipeline:** Google Drive PDF reports (Week 33, 32, 31...) and Google Sheets risk registers.
- **Historical Persistence:** `snapshots.json`, `config.json`, `risks.json`, and `issues.json` stored in the project's GCS bucket prefix (`{project}/`).
- **CLI Configuration Pull / Edit (`vi`) / Push Workflow:** Project configuration (`config.json`, including Stream 1 & Stream 2 Google Sheet URLs and Drive Folder ID) is managed via `scripts/pipeline.py`:
  - `--pull-config [file_path]`: Downloads `gs://${DATA_BUCKET}/${project}/config.json` to a local file (default `data/<project>/config.json`) so operators can edit it in `vi`.
  - `--push-config [file_path]` (alias `--upload-config`): Validates JSON schema and Workspace URL safety (`validate_google_sheet_url`, `validate_drive_folder_id`) and uploads the local file back to `gs://${DATA_BUCKET}/${project}/config.json`.
  - `--set-primary-sheet <url>`, `--set-team-google-sheet <url>`, `--set-drive-folder <id>`: 1-command shortcuts to update specific source links directly in GCS.

## 3. Access Control & Governance (Multi-Tier Architecture)
- **Identity-Aware Proxy (IAP) Web Access Layer (Primary User Interface):**
  - Web application access is secured by Google Cloud IAP, requiring corporate Google SSO.
  - Access is granted directly to **Google Groups**:
    - `monaro-risk-dev@google.com`: Development and operator access.
    - `monaro-risk-prod@google.com`: Executive stakeholder and viewer access (e.g. `allins@google.com`).
  - Day-to-day user onboarding/offboarding is handled via the standard [Google Groups UI](https://groups.google.com/a/google.com/g/monaro-risk-dev), instantly granting or revoking IAP access without requiring GCP IAM modifications.
- **Corporate Infrastructure & TwoSync Synchronization Layer:**
  - **Ganpati (MDB) Prod Groups** (`%monaro-risk-admin.prod`, `%monaro-risk-dev.prod`, `%monaro-risk-prod.prod`) govern Nexus GCP project ownership, Cloud Build permissions, and service accounts.
  - **TwoSync** bridges internal Ganpati MDB rosters to Google Groups (`@twosync.google.com` / `@google.com`).
- **Data-Layer Permissions (Google Drive & Sheets):**
  - Team Google Sheets and Drive Shared Folders inherit group-level access rosters. Users outside the authorized groups receive standard `403 Permission Denied` errors.

## 4. Multi-Notebook Knowledge Base & Ingestion
- **Knowledge Catalog:** Project blueprints and contract deliverables are stored in `data/<project-slug>/knowledge.json` (e.g. Technical Architecture, Security ATO, Contractual SOWs).
- **Unified Ingestion:** Knowledge entries and contractual driver trees are processed and organized alongside risks and issues via the master CLI:
  `python3 scripts/pipeline.py --project=<project-slug> --sync`
- **Unified Pipeline Engine (`pipeline.py`):** Consolidated master ingestion CLI (`python3 scripts/pipeline.py --sync`).

## 5. Turnkey Operations & Handover Tooling
- **Declarative Infrastructure as Code (Terraform):** Canonical GCP infrastructure codification via reusable Terraform modules (`deploy/terraform/modules/`) covering APIs, Storage, Artifact Registry, IAM, Cloud Run, Ingestion Pipeline, Cloud Build, and Monitoring. Managed through environment roots (`deploy/terraform/environments/dev` and `prod`).
- **Root Developer Cockpit (`setup.sh`):** Unified developer interface providing pre-flight bootstrap, declarative Terraform provisioning, and sub-5s parallel cloud health auditing (`--status`, `-l`, `-m`, `--state-only`) with transparent manual checkpoints validation.
- **Automated Testing Suite:** Idiomatic `pytest` test runner (`tests/`) with root discovery via `pyproject.toml` and shared session/function fixtures in `tests/conftest.py`. Executed via `pytest` or `uv run pytest`.
- **Operator Runbook:** `docs/DEPLOYMENT_GUIDE.md` and `docs/HANDOVER_GUIDE.md` for self-service maintenance by team members (`allins@`, `sdeacon@`, `waynedavis@`).
- **Server Lifecycle:** Managed via Cloud Run in Sydney (`australia-southeast1`) and local `run_server.sh`.

## 6. Frontend Static Analysis & UI Testing Layer
- **Node.js Pre-Flight Syntax Gates:** Native AST verification (`node --check src/js/app.js src/js/app_extensions.js`) integrated into `run_server.sh` and `tests/test_frontend_integrity.py` ensuring invalid JavaScript is flagged before runtime execution.
- **ESLint 9 Flat Config (`eslint.config.js`):** Modern flat configuration enforcing ES2022 standards, browser globals, no unused expressions, and strict scoping rules across all client script assets.
- **Vitest & Happy-DOM Headless Harness (`vitest.config.js`):** Fast, headless DOM test runner (`tests/frontend/dashboard_ux.test.js`) executing against realistic dashboard fixture states (`tests/frontend/fixtures/dashboard_mock_data.js`).
  - Tests 5×5 risk matrix filtering and cell click isolation.
  - Verifies multi-register tab navigation (`Internal Risks` vs `Team Google Risks`).
  - Validates interactive modal lifecycle (opening, rendering risk details, backdrop click-to-dismiss).
  - Tests executive podcast player audio control bindings and live transcript drawer synchronization.
- **Unified Verification Script (`npm run verify`):** Single-command verification runner (`node --check`, `npm run lint`, and `npm test`) bridged directly into Python CI via `tests/test_frontend_integrity.py`.

## 7. Prompt Engineering & LLM Evaluation Architecture
- **Universal Prompt Architecture (RASCEF XML):** Production prompt templates (`prompts/exec_summary_prompt.md`, `prompts/podcast_prompt.md`) standardized on canonical XML boundary delimiters (`<role>`, `<context>`, `<instructions>`, `<guardrails>`) with internal Markdown formatting, adhering to Google Prompt Engineering Standards (`go/si-guide`, DARE framework).
- **Frontier Reasoning Optimization (Gemini 3):** Standardized on `gemini-3.5-flash` with categorical `thinking_level` (`HIGH` for executive decision synthesis, `LOW` for dual-host podcast dialogue, `MINIMAL` for multimodal report inspection), omitting legacy custom temperature parameters.
- **Tier 1 Prompt Integrity & Variable Coverage Suite (`tests/test_prompt_integrity.py`):** Automated unit test suite verifying:
  - 100% template variable resolution (ensuring 0 orphaned `{{VARIABLE}}` tokens remain after substitution).
  - Graceful fallback for sparse or empty input payloads.
  - Runtime re-coupling: ensuring `generate_multispeaker_podcast` dynamically loads `prompts/podcast_prompt.md` via `build_podcast_prompt` instead of relying on inlined hardcoded prompt strings.
- **Autonomous Advisory Auditing (`prompt-critic`):** Integrated with the background `prompt-critic` subagent for non-destructive semantic audits across the 5 canonical evaluation dimensions (Factual Grounding, Safety Boundaries, Tone/Cadence, Instruction Adherence, and Injection Resilience).


