# 🚀 Project Dash — Decoupled Risk Intelligence & Governance Platform

An ultra-responsive, decoupled executive governance and operational risk intelligence platform. Project Dash provides real-time 5×5 risk heatmaps, interactive burndown velocity curves, contractual driver trees, and integrated **Google Gemini AI** executive briefings with dual-speaker audio podcasts.

---

## 🌟 Key Architecture & Capabilities

1. **Decoupled Architecture & Multi-Project Routing**:
   - Pure client-side SPA (`index.html`) using Tailwind CSS and Chart.js.
   - 100% decoupled from project-specific content — dynamic project routing via query parameters: `?project=sample` (Project Aurora public showcase) or `?project=<your-project>`.
   - Can be served via Python server, Nginx, GitHub Pages, or serverless containers (Cloud Run).

2. **Gemini Ingestion & Decision Synthesis Engine**:
   - Ingestion CLI (`scripts/sync_drive.py` and `scripts/pipeline.py`) automatically ingests Google Sheets, Google Drive PDF report packs, and knowledge documents into standardized project datasets (`snapshots.json`, `risks.json`, `issues.json`).
   - Uses **Gemini 3.5 Flash** to generate authoritative, exception-first executive decision syntheses covering overall program posture, core health milestones, and active delivery blockers.
   - Automatically surfaces **Top 3 Critical Action Cards** (Action / Impact / Outcome) and early-warning **Sleeper Outliers** with operational rationale and interactive drill-downs.

3. **Dual-Speaker Executive Briefing (Chirp 3 HD) & Cloud Audio Storage**:
   - Synthesizes dynamic dual-host executive briefings (Alex, Program Delivery Analyst & Jordan, Technical Director) using **Gemini 3.5 Flash** (`gemini-3.5-flash`) paired with studio-grade **Google Cloud TTS Chirp 3 HD** neural voices (`en-AU-Chirp3-HD-Puck` and `en-AU-Chirp3-HD-Aoede`).
   - Integrated executive audio player with synchronized live transcript drawer, dynamic turn duration alignment, dual speaker avatars, variable playback speed, and browser speech synthesis fallback when offline.
   - Synchronously persists `.mp3` audio files to local assets and streams assets directly to Google Cloud Storage (`gs://monaro-risk-dev-data/`).

4. **Multi-Register 5×5 Risk & Issue Matrix & Clean Register Isolation**:
   - Explicitly separated tabs for **Internal Risks** (107 primary items) and **Team Google Risks** (12 technical items) with dedicated matrices, provenance tooltips, and ownership filters.
   - Dynamic Inherent vs. Residual risk matrix toggling with active cell focus rings and 1-click filtering (`↗`).
   - Longitudinal risk burndown and net backlog velocity tracking across Weekly, Bi-Weekly, and Monthly granularities.

5. **Global "Google Need-to-Know" & "Looking Around the Corner" Strategic Advisory**:
   - Persistent top-level **Google Need-to-Know** notification banner visible across all tabs with collapsible state persistence.
   - **Looking Around the Corner (30-60 Day Horizon)** predictive advisory in the Executive Summary synthesizing supply chain lead times, cross-register gaps, and PDR concurrency traps.
   - Smart CD1 Driver Tree deep-linking that opens full interactive Risk Detail Modals directly from deliverable cards.

6. **Knowledge Base & Solution Blueprints**:
   - Deep contract traceability and technical blueprint catalog mapping deliverable bundles to active risks.

---

## 🚀 Quickstart

### 1. Prerequisites
- **Python 3.12+**
- **Google Cloud ADC** (`gcloud auth application-default login`) or **`GEMINI_API_KEY`** (Required for Gemini 3.5 Flash AI decision synthesis and podcast generation; configured in `us-central1`)

### 2. Setup
```bash
# Clone the repository
git clone https://github.com/your-org/project-dash.git
cd project_dash

# Copy environment template
cp .env.example .env

# Authenticate with Google Cloud ADC for Vertex AI Gemini:
gcloud auth application-default login
```

### 3. Deployment Environments & Operational Tiers

Project Dash runs across **three distinct environments** with strict separation of access, deployment mechanics, and operational risk:

| Tier & Environment | Hosting & Live Endpoint | Access & Audience | Deployment Trigger | Impact of a Change or Bug |
| :--- | :--- | :--- | :--- | :--- |
| **1. Cloud Run Production** (`monaro-risk-dash-prod`) | **Sydney (`australia-southeast1`)**<br>[👉 Prod Dashboard](https://monaro-risk-dash-prod-525025654699.australia-southeast1.run.app/?project=monaro) | **Production Stakeholders Only**<br>Restricted via Google Cloud Identity-Aware Proxy (IAP) with Google SSO (`monaro-risk-prod@google.com`). For executive leadership, program directors, and steering committee members. | **Git Release Tags Only**<br>Triggered strictly when a production release tag is pushed on `dev` (e.g. `git tag project_dash/prod-v1.0.0 && git push origin project_dash/prod-v1.0.0`). | 🔴 **Critical / High Impact**<br>Directly impacts live executive governance decisions, contractual milestone tracking, and steering committee reporting. |
| **2. Cloud Run Development** (`monaro-risk-dash-dev`) | **Sydney (`australia-southeast1`)**<br>[👉 Dev Dashboard](https://monaro-risk-dash-dev-525025654699.australia-southeast1.run.app/?project=monaro) | **Developers & Testers Only**<br>Restricted via Google Cloud Identity-Aware Proxy (IAP) with Google SSO (`monaro-risk-dev@google.com`). For engineering operators, dashboard testers, and staging validation. | **Push to `dev` Branch**<br>Triggered automatically by Cloud Build on every push to the `dev` branch (runs automated unit tests, builds container, and updates Cloud Run). | 🟡 **Low / Contained Impact**<br>Isolated staging sandbox to validate new features, ingestion pipelines, and GCS volume mounts before tagging production. |
| **3. Local Development Server** (`server.py`) | **Local Workstation / Cloudtop**<br>`http://localhost:9000/?project=monaro`<br>`http://uk-bh-cloudtop.c.googlers.com:9000` | **Developer Only (Local Only)**<br>Bound to localhost / Cloudtop session. **Strictly viewable by the active developer**; cannot be accessed by external users or project stakeholders. | **Manual Execution**<br>Run on-demand by the developer via `python3 server.py` or `./run_server.sh`. | 🟢 **Zero External Impact**<br>Sandboxed entirely to local iteration, rapid debugging, offline UI development, and running unit tests (`pytest`). |

> [!TIP]
> **Decoupled CI/CD Architecture**:
> - **GitHub Actions CI** ([`.github/workflows/deploy_monaro_dashboard.yml`](file:///usr/local/google/home/brendanhills/dev/uk-bh-experiments/.github/workflows/deploy_monaro_dashboard.yml)): Runs automated `pytest` test suites on every PR and push with zero GCP credentials/secrets required.
> - **Google Cloud Build CD** ([`deploy/cloudbuild.yaml`](file:///usr/local/google/home/brendanhills/dev/uk-bh-experiments/project_dash/deploy/cloudbuild.yaml)): Native privileged deployment pipeline deploying container images to Cloud Run in Sydney (`australia-southeast1`).

### 4. Run the Local Development Server (Developer Only)

> [!NOTE]
> **Developer-Only Local Session**: The local Python server runs on port 9000 and is **local only and viewable exclusively by the developer**. External users and stakeholders cannot access this server. For shared or formal access, stakeholders use the IAP-secured Cloud Run Production or Development environments above.

```bash
# Start the local development server on port 9000 (serves static assets with no-cache headers)
python3 server.py

# Or use the background runner script:
./run_server.sh
```

### 5. Open in Browser & Freshness Verification (Local)
1. Open your browser at:
   - 👉 **Monaro Live**: `http://localhost:9000/?project=monaro` (or `http://uk-bh-cloudtop.c.googlers.com:9000/?project=monaro`)
   - 👉 **Sample Showcase**: `http://localhost:9000/?project=sample`
2. **Data Provenance Hub**: Click **"Workspace Sync"** in the top navigation header to view verified data provenance across Google Sheets, Drive status report archives, and NotebookLM blueprints.
3. **Checking for Updates**: In the Provenance Hub, click **"↻ Check for Updates"** (`checkForUpdates()`). The browser checks `snapshots.json` using non-cached query timestamps, smoothly reloading the dashboard if new weekly data was published by the ingestion pipeline.

### 6. Environment Setup & State Inspection Engine (`setup.sh`)

The repository root includes [`setup.sh`](./setup.sh), an idempotent CLI tool for both **turnkey infrastructure provisioning** and **sub-5s parallel state inspection** across Development (`monaro-risk-dev`) and Production (`monaro-risk-prod`) environments in Sydney (`australia-southeast1`).

#### A. Read-Only State Inspection Mode (`-l`, `--list`, `--status`)
Run `./setup.sh -l` to instantly inspect and verify the live state of all 46 tracked project assets without mutating cloud resources:

```bash
# Inspect all 46 resources (APIs, IAM, Cloud Run, IAP, Monitoring, Drive) in < 5 seconds:
./setup.sh -l --env dev
./setup.sh -l --env prod

# Filter strictly to missing or unhealthy resources (highlighted in amber/yellow):
./setup.sh -l --env dev -m

# Output canonical machine-readable state addresses (matching terraform state list format):
./setup.sh -l --env dev --state-only
```

**Key Inspection Features**:
- **High-Speed Parallel Execution**: Dispatches audit checks simultaneously across background subshells, auditing 46 cloud resources in under 5 seconds rather than minutes.
- **Structured Address Schema**: Resources follow standard canonical addresses (`category.resource_id`):
  - `gcp_api.<service>` (16 required Google Cloud APIs)
  - `iam_service_account.<email>` & `iam_binding.<role>` (Deployer identity and 9 least-privilege roles)
  - `gar_repo.<name>` (Artifact Registry repository in Sydney)
  - `cloudbuild_trigger.<name>` (Automated CI/CD build triggers)
  - `notification_channel.<type>` & `monitoring_policy.<name>` (Admin alerting channels & 5xx error policies)
  - `cloud_run_service.<name>` & `run_invoker_binding.<member>` (Web service and SSO invoker bindings)
  - `iap_web_binding.<member>` (Identity-Aware Proxy Google SSO access policies)
  - `cloud_run_job.<name>`, `cloud_tasks_queue.<name>`, `cloud_scheduler_job.<name>` (Ingestion cron pipeline)
  - `drive_access.folder_read` (Google Drive report pack folder reader access)
- **Visual Ergonomics**: Missing resources and status counts are visually emphasized with warm amber/yellow highlighting for rapid diagnosis.
- **Inherited Access Awareness**: Correctly accounts for group memberships (`@google.com`) and broad parent roles (`roles/storage.admin`) so inherited permissions are accurately evaluated.

#### B. Turnkey Environment Provisioning Mode
```bash
# Provision all 46 resources end-to-end (idempotent, self-healing, guarantees 0 missing items):
./setup.sh --env dev
./setup.sh --env prod

# Enable only the 16 required Google Cloud APIs:
./setup.sh --env dev --apis-only

# Override notification email or Google Drive folder ID:
./setup.sh --env dev --admin-email "alerts@example.com" --folder-id "<DRIVE_FOLDER_ID>"
```

---

## 🔄 Data Synchronization, Scheduled Ingestion & Refresh Architecture

Project Dash separates **data ingestion** from **web presentation** for security, zero-downtime reliability, and high performance:

```
[Google Drive Status Reports] ──> [Cloud Run Job: monaro-risk-sync-job]
[Google Sheets Risk Register]        │ (scripts/sync_drive.py + Gemini 3.5 Flash)
                                     ▼
                      [data/monaro/snapshots.json]
                                     │
                                     ▼
                   [Cloud Run Web App & REST API Server]
                                     ▲
                                     │ (Client Cache-Busting: checkForUpdates())
                               [User Browser]
```

### 1. How Data is Ingested and Synced
- **Automated Drive Discovery**: The worker script (`scripts/sync_drive.py`) interfaces with Google Drive API v3 to scan the active reports folder (`1JIsbi35mXn4W-NxjbLTWo22FQMv_zv-C`).
- **Incremental Filtering**: Reports are matched by week number against `data/monaro/snapshots.json`. Already-ingested weeks are skipped.
- **Multimodal AI Analysis**: Newly published weekly PDF packs are processed with **`gemini-3.5-flash`** to extract structured executive summaries, risk delta distributions, top 3 critical action cards, and sleeper outlier alerts.
- **Atomic Snapshots**: Updates are committed to `data/monaro/snapshots.json` and `config.json`.

### 2. How Data is Refreshed in the Client UI
- The web application serves static JSON files (`data/<project>/snapshots.json`, `risks.json`, etc.).
- When new reports are processed by the ingestion worker, users do **not** need to restart the server or reload the page:
  - Users can click **"Workspace Sync"** $\rightarrow$ **"↻ Check for Updates"**.
  - The client issues a non-cached fetch: `fetch('data/monaro/snapshots.json?t=' + Date.now(), { cache: 'no-store' })`.
  - The client updates in-memory snapshots (`TIME_MACHINE_SNAPSHOTS`) and automatically re-renders the 5×5 heatmaps, KPI metrics, and burndown charts dynamically.

### 3. How to Manage the Scheduled Task & Trigger Updates

Ingestion is managed as an automated, serverless Google Cloud pipeline in Sydney (`australia-southeast1`):

- **Cloud Run Job (`monaro-risk-sync-job`)**:
  Packaged via the unified container (`deploy/Dockerfile`) and runs in `australia-southeast1` using `github-deployer@monaro-risk-dev.iam.gserviceaccount.com`.
- **Cloud Scheduler (`monaro-sync-schedule`)**:
  Configured to trigger the sync pipeline on a regular recurring cadence (every Friday at 5:00 PM Sydney time `0 17 * * 5`).
- **Cloud Tasks Queue (`monaro-sync-queue`)**:
  Enforces a concurrency limit of `1` and retry policies to prevent duplicate simultaneous executions.

---

#### 👁️ Viewing the Scheduled Task in the Cloud Console
You can inspect the scheduled pipeline across three console dashboards:

| Component | Console Navigation | Direct Link (Pantheon / GCP) |
| :--- | :--- | :--- |
| **Cloud Scheduler** | **Cloud Scheduler > Jobs** | [Pantheon Cloud Scheduler](https://pantheon.corp.google.com/cloudscheduler?project=monaro-risk-dev) • [Public Console](https://console.cloud.google.com/cloudscheduler?project=monaro-risk-dev) |
| **Cloud Run Jobs** | **Cloud Run > Jobs** | [Pantheon Cloud Run Jobs](https://pantheon.corp.google.com/run/jobs?project=monaro-risk-dev) • [Public Console](https://console.cloud.google.com/run/jobs?project=monaro-risk-dev) |
| **Cloud Tasks** | **Cloud Tasks > Queues** | [Pantheon Cloud Tasks](https://pantheon.corp.google.com/cloudtasks?project=monaro-risk-dev) • [Public Console](https://console.cloud.google.com/cloudtasks?project=monaro-risk-dev) |
| **Live Job Logs** | **Logging > Logs Explorer** | [Pantheon Logs Explorer](https://pantheon.corp.google.com/logs/query;query=resource.type%3D%22cloud_run_job%22%20AND%20resource.labels.job_name%3D%22monaro-risk-sync-job%22?project=monaro-risk-dev) |

---

#### ⚡ How to Trigger an Update Manually (On-Demand)

You can trigger an update out-of-cycle at any time using either the Cloud Console UI or the terminal:

##### Method 1: Execute Directly from Cloud Run Jobs Console (Recommended for 1-Click Run & Live Logs)
1. Open the **[Cloud Run Jobs Console](https://pantheon.corp.google.com/run/jobs?project=monaro-risk-dev)**.
2. Click on **`monaro-risk-sync-job`** in the list.
3. In the top action bar, click the **`▶ Execute`** button.
   - *Tip*: Clicking the dropdown arrow next to "Execute" allows you to select **"Execute with overrides"** if you want to temporarily test with custom environment variables (e.g. `DEFAULT_PROJECTS=sample` or custom log levels).
4. The console automatically redirects to the **Executions** tab, displaying the live execution status (`Pending` $\rightarrow$ `Running` $\rightarrow$ `Succeeded`) and real-time streaming container logs.

##### Method 2: "Force Run" from Cloud Scheduler Console (Tests Full Cron Trigger)
1. Open the **[Cloud Scheduler Console](https://pantheon.corp.google.com/cloudscheduler?project=monaro-risk-dev)**.
2. Locate the row for **`monaro-sync-schedule`**.
3. Click the three vertical dots (**`⋮`**) on the far right and select **`Force run`**.
4. The job status will update to `Success` and will dispatch the HTTP POST request to Cloud Run, spawning a new worker execution asynchronously.

##### Method 3: Trigger via `gcloud` CLI in Terminal
```bash
# Option A: Execute the Cloud Run Job directly and stream output to your terminal:
gcloud run jobs execute monaro-risk-sync-job \
  --region=australia-southeast1 \
  --project=monaro-risk-dev \
  --wait

# Option B: Fire the Cloud Scheduler cron trigger:
gcloud scheduler jobs run monaro-sync-schedule \
  --location=australia-southeast1 \
  --project=monaro-risk-dev
```

##### Method 4: Ingestion & Verification CLI Scripts
```bash
# Trigger remote Cloud Run Job in GCP via Python helper:
python3 scripts/trigger_sync.py --mode=cloud --project=monaro-risk-dev --region=australia-southeast1

# Run pre-flight diagnostics (verifies Drive, Vertex AI Gemini, Storage, and Schemas):
python3 scripts/sync_drive.py --doctor

# Run local standalone ingestion using local ADC credentials:
python3 scripts/sync_drive.py --project monaro

# Audit executive podcast briefing status & freshness (Gemini 3.5 Flash) across all projects:
python3 scripts/check_podcast_status.py

# Inspect specific project and automatically fix/regenerate missing or fallback podcasts:
python3 scripts/check_podcast_status.py --project monaro --fix
```

---

#### 🔧 How to Update the Process When Needed

1. **Updating Ingestion Logic, Prompts, or Dashboard Frontend**:
   - Edit scripts or frontend assets.
   - Verify locally: `pytest`.
   - Push to `dev`: `git push origin dev`.
   - The unified Cloud Build trigger in Sydney automatically runs unit tests, builds both container images (`monaro-risk-dash-dev` and `monaro-risk-sync`) with Docker layer caching, deploys the web service, and updates the sync job.
   - Alternatively, trigger manually in Sydney:
     ```bash
     gcloud builds submit --config=deploy/cloudbuild.yaml --region=australia-southeast1 --project=monaro-risk-dev
     ```

2. **Changing the Schedule Timing**:
   ```bash
   # Change cron schedule (e.g. from Friday 5 PM to Monday 9 AM Sydney time):
   gcloud scheduler jobs update http monaro-sync-schedule \
     --location=australia-southeast1 \
     --project=monaro-risk-dev \
     --schedule="0 9 * * 1" \
     --time-zone="Australia/Sydney"
   ```

3. **Pausing or Resuming the Scheduled Task**:
   ```bash
   # Pause (e.g. during a program change freeze):
   gcloud scheduler jobs pause monaro-sync-schedule --location=australia-southeast1 --project=monaro-risk-dev

   # Resume:
   gcloud scheduler jobs resume monaro-sync-schedule --location=australia-southeast1 --project=monaro-risk-dev
   ```


---

## 📁 Directory Structure & Multi-Project Isolation

All project-specific data is strictly isolated inside the `data/<project-slug>/` directory:

```
project_dash/
├── index.html                   # Zero-build single-file frontend presentation engine
├── server.py                    # Static development server with no-cache headers
├── .env.example                 # Environment configuration template
├── setup.sh                     # Canonical turnkey provisioning & sub-5s state inspection (-l) tool
├── deploy/                      # Infrastructure & Container deployment configs
│   ├── Dockerfile               # Unified Python 3.13 Cloud Run web service & sync container
│   ├── cloudbuild.yaml          # Streamlined automated Cloud Build CI/CD pipeline (~45s)
├── docs/                        # Project operator manuals & guides
│   ├── HANDOVER_GUIDE.md        # Turnkey operator & handover manual
│   ├── TEAM_PRESENTATION_GUIDE.md # 5-minute showcase narrative
│   └── DEPLOYMENT_GUIDE.md      # Automated CI/CD, IAP security & Runbooks
├── prompts/
│   ├── exec_summary_prompt.md   # Gemini structured JSON executive summary prompt
│   └── podcast_prompt.md        # Gemini dual-speaker podcast script prompt
├── scripts/
│   ├── sync_drive.py            # Turnkey standalone Google Drive & Sheets ingestion engine
│   ├── trigger_sync.py          # Admin/Dev CLI trigger tool for Cloud Run Job & local sync
│   ├── pipeline.py              # Ingestion, Drive report parsing & Gemini synthesis pipeline
│   ├── gemini_generator.py      # Gemini 3.5 Flash synthesis & podcast dialogue generator
│   ├── check_podcast_status.py  # Standalone CLI audit tool to inspect & refresh podcast status
│   └── check_build_status.py    # Cloud Build CI/CD status query tool
├── src/
│   └── js/                      # Modular ES6 frontend architecture (api.js, state.js, analytics.js, app.js)
├── data/
│   └── sample/                  # Public showcase dataset (Project Aurora)
│       ├── config.json          # Project branding, theme colors, feature flags
│       ├── risks.json           # 5x5 Inherent & Residual risk registry
│       ├── issues.json          # Operational issue register
│       ├── snapshots.json       # Longitudinal weekly snapshots (W22-W27)
│       ├── knowledge.json       # Blueprint & contract knowledge sources
│       └── driver_tree.json     # Contractual milestones & capability drops
└── tests/                       # Complete automated unit test suite (165 tests)
```

---

## 🧪 Testing & Quality Assurance

Project Dash includes a comprehensive, idiomatic `pytest` suite covering data integrity, live client calculations, Gemini generation, server endpoints, and frontend decoupling:

```bash
# Run all automated tests (181 tests)
pytest

# Run specific test suites
pytest tests/test_gemini_generator.py
pytest tests/test_pipeline.py
pytest tests/test_server_parameterized.py
```


---

## 🚢 CI/CD & Deployment Architecture

Project Dash is deployed automatically to Google Cloud Run in Sydney, Australia (**`australia-southeast1`**) via Cloud Build:

- **Development (`monaro-risk-dash-dev`)**: Triggered automatically on pushes to the `dev` branch.
- **Production (`monaro-risk-dash-prod`)**: Triggered automatically when release tags matching `^project_dash/prod-.*$` (e.g. `project_dash/prod-v1.0.0`) are pushed on `dev`.
- **Pipeline Efficiency & Default Worker Pool**: Operates a streamlined 5-stage pipeline using Cloud Build's default standard warm pool in Sydney (~71s end-to-end turnaround, ~52s step execution, ~2s queue time, and eligible for 120 free build-minutes/day).
- **Documentation / No-Build Pushes**: To push documentation or workflow updates without triggering a Cloud Run build, include `[skip ci]` or `[ci skip]` in your commit message:
  ```bash
  git commit -m "docs: update runbooks [skip ci]"
  git push origin dev
  ```
### 🧭 Quick Navigation: Live Dashboards & Google Cloud Console

| Resource | Development (`monaro-risk-dev`) | Production (`monaro-risk-prod`) | Local Development |
| :--- | :--- | :--- | :--- |
| **Live Deployed Dashboard** | • [👉 Monaro Live (Sydney)](https://monaro-risk-dash-dev-525025654699.australia-southeast1.run.app/?project=monaro)<br>• [👉 Aurora Showcase (Sydney)](https://monaro-risk-dash-dev-525025654699.australia-southeast1.run.app/?project=sample) | • [👉 Monaro Live (Prod)](https://monaro-risk-dash-prod-525025654699.australia-southeast1.run.app/?project=monaro)<br>• [👉 Aurora Showcase (Prod)](https://monaro-risk-dash-prod-525025654699.australia-southeast1.run.app/?project=sample) | • [Local Monaro](http://uk-bh-cloudtop.c.googlers.com:9000/?project=monaro)<br>• [Local Aurora](http://uk-bh-cloudtop.c.googlers.com:9000/?project=sample) |
| **Cloud Run Services** | [👉 Cloud Run Console (Dev)](https://pantheon.corp.google.com/run?project=monaro-risk-dev) | [👉 Cloud Run Console (Prod)](https://pantheon.corp.google.com/run?project=monaro-risk-prod) | — |
| **Cloud Build Triggers** | [👉 Build Triggers (Dev)](https://pantheon.corp.google.com/cloud-build/triggers?project=monaro-risk-dev) | [👉 Build Triggers (Prod)](https://pantheon.corp.google.com/cloud-build/triggers?project=monaro-risk-prod) | — |
| **Cloud Build History** | [👉 Build History (Dev)](https://pantheon.corp.google.com/cloud-build/builds?project=monaro-risk-dev) | [👉 Build History (Prod)](https://pantheon.corp.google.com/cloud-build/builds?project=monaro-risk-prod) | — |
| **Artifact Registry** | [👉 Docker Images (Dev)](https://pantheon.corp.google.com/artifacts?project=monaro-risk-dev) | [👉 Docker Images (Prod)](https://pantheon.corp.google.com/artifacts?project=monaro-risk-prod) | — |
| **Cloud Logging** | [👉 Logs Explorer (Dev)](https://pantheon.corp.google.com/logs/query?project=monaro-risk-dev) | [👉 Logs Explorer (Prod)](https://pantheon.corp.google.com/logs/query?project=monaro-risk-prod) | — |

- **Deployment, Provisioning & Operations**: See [`docs/DEPLOYMENT_GUIDE.md`](./docs/DEPLOYMENT_GUIDE.md) for the comprehensive canonical guide: automated CI/CD pipelines, turnkey environment provisioning (`./setup.sh`), production release tag workflows, and SRE Day-2 runbooks.
- **Cloud Services, APIs & Running Costs**: See [`docs/CLOUD_COSTS_AND_API_REVIEW.md`](./docs/CLOUD_COSTS_AND_API_REVIEW.md) for an audit of all 14 GCP APIs, workload modeling for 10–50 daily users, itemized Sydney running costs (<$1.00/month), and cost optimization recommendations.

### 💰 Cloud Running Costs & Free Tier Economics
- **Expected Baseline Spend**: **<$1.00 AUD / month** under moderate organizational usage (10–50 users, ~22,000 requests/month, ~4 GB egress).
- **100% Free Tier Coverage**: Cloud Run web requests (first 2M free), Cloud Run compute (first 180k vCPU-s free), Identity-Aware Proxy (native Cloud Run $0.00), Network egress (first 100 GB free), and Cloud Build (first 120 min/day free) operate entirely within permanent GCP Free Tier allowances.
- **Cold Start vs. Hot Standby**: With `--min-instances=0` (scale-to-zero), idle cost is **$0.00** with a fast ~1.5s to 2.0s cold start for the Python 3.13-slim container. Setting `--min-instances=1` guarantees 0ms latency at ~$12.50/month in Sydney.
- **Active Guardrails**: Browser caching headers via `server.py`, automated image lifecycle cleanup policies (`deploy/cleanup-policy.json`), and default warm worker pools prevent storage and billing drift.

---

## 🔒 Security & Privacy

- **Strict Isolation**: Proprietary datasets (such as `data/monaro/` or `data/local/`) and secret keys (`.env`) are excluded in `.gitignore`.
- **Zero Hardcoded Secrets**: Gemini API calls support standard Google Cloud Application Default Credentials (ADC) or environment-managed keys.

---

## 📄 License
Licensed under the Apache 2.0 License.
