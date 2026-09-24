# 🛠️ Project Dash — Administrator & Developer Guide

This manual is written for engineers and SREs experienced with Google Cloud (`gcloud`, Cloud Run, Cloud Build, IAP, Terraform) and Linux (`bash`, `git`, `uv`, `npm`). It documents **only** the project-specific architecture, operational invariants, CLI workflows, and developer conventions needed to keep **Project Dash** running and extend its features.

---

## 1. Critical Invariants & Operational Gotchas

> [!CAUTION]
> ### 🚨 1. 90-Day Sandbox Project Expiration (`15 November 2026`)
> Both `monaro-risk-dev` and `monaro-risk-prod` were provisioned on **17 August 2026** as 90-day temporary GCP projects and will be **suspended/deleted on Sunday, 15 November 2026 (15:27 AEST)** unless linked to a permanent billing account:
> ```bash
> gcloud beta billing projects link monaro-risk-prod --billing-account=<PERMANENT_BILLING_ACCOUNT_ID>
> gcloud beta billing projects link monaro-risk-dev  --billing-account=<PERMANENT_BILLING_ACCOUNT_ID>
> ```

### 2. Environment & Infrastructure Matrix (`australia-southeast1`)

| Resource | Development (`monaro-risk-dev`) | Production (`monaro-risk-prod`) |
| :--- | :--- | :--- |
| **Cloud Run Web Service** | `monaro-risk-dash-dev` ([Open](https://monaro-risk-dash-dev-525025654699.australia-southeast1.run.app/?project=monaro)) | `monaro-risk-dash-prod` ([Open](https://monaro-risk-dash-prod-525025654699.australia-southeast1.run.app/?project=monaro)) |
| **Cloud Run Sync Job** | `monaro-risk-sync-job` (`python scripts/sync_drive.py`) | `monaro-risk-sync-job` (`python scripts/sync_drive.py`) |
| **Scheduler / Queue** | `monaro-sync-schedule` (`0 17 * * 5` Sydney) $\rightarrow$ `monaro-sync-queue` | `monaro-sync-schedule` (`0 17 * * 5` Sydney) $\rightarrow$ `monaro-sync-queue` |
| **Authoritative GCS Bucket** | `gs://monaro-risk-dev-data/` (mounted at `/app/data`) | `gs://monaro-risk-prod-data/` (mounted at `/app/data`) |
| **Deployer Service Account** | `github-deployer@monaro-risk-dev.iam.gserviceaccount.com` | `github-deployer@monaro-risk-prod.iam.gserviceaccount.com` |
| **IAP / Ganpati Groups** | `monaro-risk-dev@google.com` (`%monaro-risk-dev.prod`) | `monaro-risk-prod@google.com` (`%monaro-risk-prod.prod`) |
| **CD Trigger** | Push to `dev` branch (`deploy-monaro-risk-dash-dev`) | Push tag matching `^project_dash/prod-.*$` (`deploy-monaro-risk-dash-prod`) |

### 3. Non-Obvious System Quirks

1. **Unified Container Architecture (`deploy/Dockerfile`)**:
   - Uses `python:3.13-slim` (not Nginx).
   - **Web Service**: Runs `CMD ["python", "server.py"]` on port `8080`, serving the static SPA (`index.html`, `src/js/`) and JSON/MP3 assets from `/app/data` (or GCS fallback) with `Cache-Control: no-store, no-cache`.
   - **Ingestion Job**: Reuses the exact same image with `--command=python,scripts/sync_drive.py --args=--project=monaro`.
2. **Cloud Build `CLOUD_LOGGING_ONLY` Diagnostics**:
   - [`deploy/cloudbuild.yaml`](../deploy/cloudbuild.yaml) enforces `logging: CLOUD_LOGGING_ONLY` and builds on the default standard warm worker pool in `australia-southeast1` (~52s build time).
   - Because no GCS `logsBucket` is used, `gcloud builds log <BUILD_ID>` fails with `Build does not specify logsBucket`. Always inspect builds using the dedicated CLI helper (which queries Cloud Logging and extracts `statusDetail` for pre-execution webhook/trigger failures):
     ```bash
     python3 scripts/check_build_status.py --project monaro-risk-dev --limit 5
     ```
3. **Dual Git Remotes (`origin` & `depot`) & Mandatory SSH Commit Signing**:
   - `origin` (`git@github.com:brendanhills/uk-bh-project-dash.git`) and `depot` (`git@depot.code.corp.goog:sovops-au/monaro-dash.git`) are pushed in tandem on the **`dev`** trunk branch (`origin/main` enforces GitHub `GH013` protection; `depot` enforces `@google.com` email and **verified ED25519 SSH signatures** via `git commit -S`).
   - To push documentation-only updates without triggering Cloud Build, include `[skip ci]` in the commit message.
4. **IAP Dual-Binding & Ganpati (`TwoSync`) Requirement**:
   - Cloud Run `--iap` requires **both** `roles/run.invoker` (on the Cloud Run service) and `roles/iap.httpsResourceAccessor` (on `iap_web`) for both `@google.com` and `@twosync.google.com` group principals.
   - User onboarding/offboarding is managed self-service via [Google Groups](https://groups.google.com/a/google.com/g/monaro-risk-prod) or [Ganpati](https://ganpati2.corp.google.com/group/%25monaro-risk-prod.prod) (`%monaro-risk-admin.prod` owns both `dev` and `prod` groups).
5. **Cloud Build Webhook Quirk: 404 No Common Ancestor**:
   - When branches are rebased, force-pushed, or branch histories are recreated on `dev`, Cloud Build's file-filtering trigger fails pre-execution with:
     ```text
     ListChangedFiles failed: GET https://api.github.com/.../compare/<old>...<new>: 404 No common ancestor
     ```
   - **Remediation**: Submit builds directly via `gcloud` (bypassing the GitHub compare API webhook) or use the upcoming `./deploy.sh --build` command:
     ```bash
     gcloud builds submit \
       --config=deploy/cloudbuild.yaml \
       --project=monaro-risk-dev \
       --region=australia-southeast1
     ```

---

## 2. Day-2 Operations & CLI Cheatsheet

### A. Updating Project Configuration (`config.json` in GCS)
All runtime project datasets (`config.json`, `snapshots.json`, `risks.json`, `issues.json`) and podcast `.mp3` files live authoritatively in `gs://monaro-risk-{dev|prod}-data/<project>/`. To modify sheet URLs, feature toggles, or `governance.ragThresholds`:

```bash
# 1. Download authoritative config.json from GCS to local data/<project>/config.json
python3 scripts/pipeline.py --pull-config --project monaro

# 2. Edit configuration locally
vi data/monaro/config.json

# 3. Validate HTTPS Sheet URLs/schema, synchronize primaryRegisterSheet <-> googleSheets.sheetUrl, and upload to GCS
python3 scripts/pipeline.py --push-config --project monaro
```

### B. Environment Health Inspection & Provisioning (`setup.sh` & Terraform)
[`setup.sh`](../setup.sh) wraps declarative Terraform IaC ([`deploy/terraform/`](../deploy/terraform/)) and runs a sub-5-second parallel state audit across all **46 tracked GCP resources** (16 APIs, 9 IAM bindings, Artifact Registry, Cloud Build triggers, Cloud Run service/job, IAP bindings, Cloud Tasks, Cloud Scheduler, Monitoring alerts, and Drive folder permissions):

```bash
# Read-only parallel inspection (< 5s) of all 46 cloud assets + manual checkpoints
./setup.sh -l --env dev
./setup.sh -l --env prod -m          # Show only missing/unhealthy resources

# Declarative provisioning via setup.sh or directly via Terraform
./setup.sh --env dev
cd deploy/terraform/environments/dev && terraform init && terraform plan
```

### C. Triggering Data Ingestion & Podcast Regeneration

```bash
# 1. Execute the Cloud Run Ingestion Job on-demand in Sydney
gcloud run jobs execute monaro-risk-sync-job --region=australia-southeast1 --project=monaro-risk-dev --wait

# 2. Run pre-flight diagnostics locally (checks Drive API, Vertex AI Gemini 3.5 Flash in australia-southeast1, GCS, & schemas)
python3 scripts/sync_drive.py --doctor

# 3. Audit executive podcast audio freshness and regenerate missing/fallback MP3s (Chirp 3 HD: Puck & Aoede)
python3 scripts/check_podcast_status.py --project monaro --fix

# 4. Register & sync an additional NotebookLM / Gemini Notebook source into data/notebooks/registry.json
python3 scripts/pipeline.py --notebook-id "<UUID>" --title "Architecture Blueprints" --slug "tech_blueprints" --category "Engineering"
```

### D. Promoting to Production, Rollbacks & Emergency Shutdown

```bash
# Promote current dev commit to Production (triggers deploy-monaro-risk-dash-prod)
git tag -s project_dash/prod-v1.x.y -m "Release v1.x.y"
git push origin project_dash/prod-v1.x.y && git push depot project_dash/prod-v1.x.y

# Instant zero-downtime traffic rollback to previous Cloud Run revision
gcloud run services update-traffic monaro-risk-dash-prod --to-revisions=monaro-risk-dash-prod-000XX-abc=100 --region=australia-southeast1 --project=monaro-risk-prod

# Emergency stop (shifts 0% traffic immediately)
./setup.sh --stop --env prod
```

---

## 3. Developer Guide: Architecture & Adding a Feature

### 1. Codebase Layout

```text
project_dash/
├── index.html                   # SPA DOM shell, Tailwind styling, and inline onclick="..." bindings
├── server.py                    # Python HTTP & REST server (serves SPA, /data/* from local/GCS, and /api/* routes)
├── run_server.sh                # Tmux lifecycle wrapper (:9000) with <15ms node --check AST pre-flight gate
├── setup.sh                     # Parallel GCP state inspector (-l) and environment provisioner
├── src/js/
│   ├── app.js                   # Primary frontend controller, data loader, and window.* global bindings
│   ├── state.js                 # Centralized reactive state store (store.get / store.set)
│   ├── analytics.js             # 5x5 matrix scoring, KPI math, and text sanitization helpers
│   ├── charts.js                # Chart.js timeline & burndown instances
│   └── modules/                 # Modular ES6 view controllers:
│       ├── exec_briefing.js     # Tab 1: Executive Cockpit, Gemini summary, Top 3 cards, podcast player
│       ├── risk_heatmap.js      # Tab 2 & 4: 5x5 Inherent/Residual heatmap grids
│       ├── risk_explorer.js     # Tab 2 & 4: Faceted filtering, search, Cards vs. Compact Table views
│       ├── issue_register.js    # Tab 3: Active Issue Register table
│       ├── performance_trends.js# Tab 5: Multi-granularity burndown & cause concentration charts
│       ├── blueprint_knowledge.js# Tab 6: NotebookLM selector & Contract Annex bundle cards
│       ├── driver_tree.js       # Tab 7: CD1 / CD1.5 capability drops & Level 2/3 gate decomposition
│       ├── time_machine.js      # Header: Historical snapshot rewinding
│       └── modals.js            # Universal Item Detail modal, Data Provenance Hub, & toast notifications
├── scripts/
│   ├── sync_drive.py            # Cloud Run Job entrypoint: Drive/Sheets scanner & incremental snapshot updater
│   ├── pipeline.py              # Core ETL engine, config.json pull/push validator, & fallback synthesizer
│   ├── gemini_generator.py      # Vertex AI Gemini 3.5 Flash synthesis & Cloud TTS Chirp 3 HD audio generator
│   ├── check_podcast_status.py  # Podcast verification & regeneration CLI
│   └── check_build_status.py    # Cloud Build log & statusDetail inspector (CLOUD_LOGGING_ONLY)
├── prompts/
│   ├── exec_summary_prompt.md   # RASCEF XML prompt for executive synthesis (thinking_level="HIGH")
│   └── podcast_prompt.md        # RASCEF XML prompt for Alex & Jordan dialogue (thinking_level="LOW")
└── tests/                       # 122 Pytest unit/contract tests + tests/frontend/dashboard_ux.test.js (Vitest)
```

### 2. How to Add or Modify a Frontend UI Feature
When adding a new UI widget, filter, or tab interaction:
1. **DOM & Module Wiring (`window.*` Rule)**:
   - [`index.html`](../index.html) uses inline event attributes (e.g. `onclick="myNewHandler()"`), while [`src/js/app.js`](../src/js/app.js) and [`src/js/modules/*.js`](../src/js/modules/) execute in strict ES module scope (`"type": "module"` in `package.json`).
   - **Mandatory Step**: Any function invoked from `index.html` **must be explicitly assigned to `window` in `src/js/app.js`** (and `window.app` if called by modular templates), otherwise clicking the element in the browser or in `tests/frontend/dashboard_ux.test.js` will throw a `ReferenceError`.
2. **State & Data Isolation**:
   - Read and update state via `store` (`src/js/state.js`) and the top-level state arrays (`LIVE_RISKS`, `LIVE_TEAM_GOOGLE_RISKS`, `LIVE_ISSUES`, `TIME_MACHINE_SNAPSHOTS`) in `src/js/app.js`.
   - **Confidentiality Contract**: Never hardcode Project Monaro Drive IDs, Sheet IDs, or strings (`"Monaro"`, `"F-DSE"`) in `index.html` or `data/sample/*.json`. [`tests/test_data_and_schemas.py`](../tests/test_data_and_schemas.py) (`test_sample_data_confidentiality_isolation`) enforces strict separation between confidential `monaro` data and public `sample` data.

### 3. How to Modify Gemini Prompts (`prompts/*.md`)
1. **RASCEF XML Standard**:
   - Prompts in [`prompts/exec_summary_prompt.md`](../prompts/exec_summary_prompt.md) and [`prompts/podcast_prompt.md`](../prompts/podcast_prompt.md) must retain top-level XML delimiters (`<role>`, `<context>`, `<instructions>`, `<guardrails>`).
   - Model calls in [`scripts/gemini_generator.py`](../scripts/gemini_generator.py) target `gemini-3.5-flash` in `australia-southeast1` using categorical `thinking_level` (`HIGH` for synthesis, `LOW` for podcast dialogue, `MINIMAL` for PDF cover inspection) without custom `temperature` overrides.
2. **Template Variable Contract (`{{VARIABLE}}`)**:
   - Every `{{PLACEHOLDER}}` token in `prompts/*.md` must be substituted inside `build_executive_prompt()` or `build_podcast_prompt()` in `scripts/gemini_generator.py`.
   - [`tests/test_prompt_integrity.py`](../tests/test_prompt_integrity.py) fails CI if any unreplaced `{{...}}` token remains after rendering.

### 4. Local Development & 5-Layer Verification Gate
Before committing any code, prompt, or configuration change, run both the Node/Vitest and Python test suites:

```bash
# 1. Install / sync local toolchains (Python 3.12+ via uv, Node v22+ via npm)
uv sync && npm install

# 2. Start local dev server on http://localhost:9000/?project=monaro (runs <15ms AST syntax check first)
./run_server.sh

# 3. Run the 5-layer verification suite before committing:
npm run verify    # Layer 1: node --check AST | Layer 2: ESLint 9 Flat Config | Layer 3: 6 Vitest happy-dom UX tests
uv run pytest     # Layer 4: Frontend/Contract bridge | Layer 5: 122 Backend, Schema, & Prompt Integrity tests
```
