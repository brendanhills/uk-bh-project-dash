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
   - Uses **Gemini 3.7 Flash** to generate structured executive syntheses tailored for 3 executive stakeholder perspectives:
     - 👔 **Executive**: Focus on milestones, strategic delivery blockers, and board actions.
     - ⚙️ **Technical**: Focus on infrastructure, security enclaves, API SLAs, and telemetry.
     - ⚖️ **Governance**: Focus on commercial gates, contractual IBR audits, and ATO accreditation.
   - Highlights **Top 3 Critical Action Cards** and early warning **Sleeper Outliers**.

3. **Neural Dual-Speaker Audio Briefing**:
   - Synthesizes dual-host executive discussion podcasts using Gemini TTS (`MultiSpeakerVoiceConfig` with `Puck` and `Aoede`).
   - Built-in neural waveform player with variable playback speed, auto-scrolling synced transcript, and direct MP3 export.

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
- **Google Cloud ADC** (`gcloud auth application-default login`) or **`GEMINI_API_KEY`** (Required for Gemini 3.7 Flash AI decision synthesis and neural podcast audio generation)

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

### 3. Run the Development Server
```bash
# Start the local development server on port 9000 (serves static assets with no-cache headers)
python3 server.py

# Or use the background runner script:
./run_server.sh
```

### 4. Open in Browser & Freshness Verification
1. Open your browser at:
   - 👉 **Sample Showcase**: `http://localhost:9000/?project=sample`
   - 👉 **Monaro Live**: `http://localhost:9000/?project=monaro`
2. **Data Provenance Hub**: Click **"Workspace Sync"** in the top navigation header to view verified data provenance across Google Sheets, Drive status report archives, and NotebookLM blueprints.
3. **Checking for Updates**: In the Provenance Hub, click **"↻ Check for Updates"** (`checkForUpdates()`). The browser checks `snapshots.json` using non-cached query timestamps, smoothly reloading the dashboard if new weekly data was published by the ingestion pipeline.

---

## 🔄 Data Synchronization, Scheduled Ingestion & Refresh Architecture

Project Dash separates **data ingestion** from **web presentation** for security, zero-downtime reliability, and high performance:

```
[Google Drive Status Reports] ──> [Cloud Run Job: monaro-risk-sync-job]
[Google Sheets Risk Register]        │ (scripts/sync_drive.py + Gemini 3.7 Flash)
                                     ▼
                      [data/monaro/snapshots.json]
                                     │
                                     ▼
                       [Cloud Run Nginx Web App]
                                     ▲
                                     │ (Client Cache-Busting: checkForUpdates())
                               [User Browser]
```

### 1. How Data is Ingested and Synced
- **Automated Drive Discovery**: The worker script (`scripts/sync_drive.py`) interfaces with Google Drive API v3 to scan the active reports folder (`1JIsbi35mXn4W-NxjbLTWo22FQMv_zv-C`).
- **Incremental Filtering**: Reports are matched by week number against `data/monaro/snapshots.json`. Already-ingested weeks are skipped.
- **Multimodal AI Analysis**: Newly published weekly PDF packs are processed with **`gemini-3.7-flash`** to extract structured executive summaries, risk delta distributions, top 3 critical action cards, and sleeper outlier alerts.
- **Atomic Snapshots**: Updates are committed to `data/monaro/snapshots.json` and `config.json`.

### 2. How Data is Refreshed in the Client UI
- The web application serves static JSON files (`data/<project>/snapshots.json`, `risks.json`, etc.).
- When new reports are processed by the ingestion worker, users do **not** need to restart the server or reload the page:
  - Users can click **"Workspace Sync"** $\rightarrow$ **"↻ Check for Updates"**.
  - The client issues a non-cached fetch: `fetch('data/monaro/snapshots.json?t=' + Date.now(), { cache: 'no-store' })`.
  - The client updates in-memory snapshots (`TIME_MACHINE_SNAPSHOTS`) and automatically re-renders the 5×5 heatmaps, KPI metrics, and burndown charts dynamically.

### 3. How to Manage the Scheduled Task
Ingestion is managed as an automated Google Cloud infrastructure pipeline:

- **Cloud Run Job (`monaro-risk-sync-job`)**:
  Packaged via `deploy/Dockerfile.sync` and runs in `australia-southeast1` using the deployer service account.
- **Cloud Scheduler (`monaro-sync-schedule`)**:
  Configured to trigger the sync pipeline on a regular recurring cadence (e.g. every Friday at 5:00 PM Sydney time `0 17 * * 5`).
- **Cloud Tasks Queue (`monaro-sync-queue`)**:
  Enforces a concurrency limit of `1` and retry policies to prevent duplicate simultaneous executions.

#### Managing the Schedule with `gcloud`
```bash
# View active schedule
gcloud scheduler jobs describe monaro-sync-schedule --location=australia-southeast1 --project=monaro-risk-dev

# Update schedule frequency (e.g. every Friday at 5:00 PM AEST)
gcloud scheduler jobs update http monaro-sync-schedule \
  --location=australia-southeast1 \
  --project=monaro-risk-dev \
  --schedule="0 17 * * 5" \
  --time-zone="Australia/Sydney"

# Pause the scheduled task (e.g. during change freeze)
gcloud scheduler jobs pause monaro-sync-schedule --location=australia-southeast1 --project=monaro-risk-dev

# Resume the scheduled task
gcloud scheduler jobs resume monaro-sync-schedule --location=australia-southeast1 --project=monaro-risk-dev
```

#### On-Demand Triggering (Dev & Admin)
To force immediate synchronization out-of-cycle:
1. **Google Cloud Console (1-Click)**:
   - Navigate to [Cloud Run Jobs](https://pantheon.corp.google.com/run/jobs?project=monaro-risk-dev), select `monaro-risk-sync-job`, and click **Execute**.
   - Or navigate to [Cloud Scheduler](https://pantheon.corp.google.com/cloudscheduler?project=monaro-risk-dev) and click **Force Run**.
2. **CLI Dispatch Tool (`scripts/trigger_sync.py`)**:
   ```bash
   # Trigger remote Cloud Run Job in GCP:
   python3 scripts/trigger_sync.py --mode=cloud --project=monaro-risk-dev --region=australia-southeast1

   # Run local standalone ingestion:
   python3 scripts/trigger_sync.py --mode=local
   ```


---

## 📁 Directory Structure & Multi-Project Isolation

All project-specific data is strictly isolated inside the `data/<project-slug>/` directory:

```
project_dash/
├── index.html                   # Zero-build single-file frontend presentation engine
├── server.py                    # Static development server with no-cache headers
├── .env.example                 # Environment configuration template
├── .gitignore                   # Strict sanitization rules
├── deploy/                      # Infrastructure & Container deployment configs
│   ├── Dockerfile               # Static Nginx Cloud Run web service container
│   ├── Dockerfile.sync          # Python 3.13 Cloud Run Job ingestion worker container
│   ├── cloudbuild.yaml          # 5-stage automated Cloud Build CI/CD pipeline
│   └── provision_environment.sh # Turnkey GCP, IAP, Cloud Run Job & Cloud Tasks provisioning
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
│   ├── gemini_generator.py      # Gemini 3.7 Flash synthesis & TTS audio generator
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

## 🛠️ Adding a New Project

To add a new project (e.g. `my-project`):

1. **Create project directory**:
   ```bash
   mkdir -p data/my-project
   cp -r data/sample/* data/my-project/
   ```

2. **Customize `data/my-project/config.json`**:
   - Update `project.name`, `project.title`, `project.logoIcon`, and `theme.primaryColor`.
   - Configure data source links (`sources.googleSheets.riskRegisterUrl`, etc.).

3. **Populate your data**:
   - Update `risks.json`, `issues.json`, `snapshots.json`, `driver_tree.json`, and `knowledge.json`.

4. **Run ingestion**:
   ```bash
   python3 scripts/pipeline.py --project=my-project
   ```

5. **View in browser**:
   Navigate to `http://localhost:9000/?project=my-project`.

---

## 🧪 Testing & Quality Assurance

Project Dash includes a comprehensive, idiomatic `pytest` suite covering data integrity, live client calculations, Gemini generation, server endpoints, and frontend decoupling:

```bash
# Run all automated tests (165 tests)
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
| **Live Deployed Dashboard** | • [👉 Aurora Showcase (Sydney)](https://monaro-risk-dash-dev-525025654699.australia-southeast1.run.app/?project=sample)<br>• [👉 Monaro Live (Sydney)](https://monaro-risk-dash-dev-525025654699.australia-southeast1.run.app/?project=f-dse) | • [👉 Aurora Showcase (Prod)](https://monaro-risk-dash-prod-525025654699.australia-southeast1.run.app/?project=sample)<br>• [👉 Monaro Live (Prod)](https://monaro-risk-dash-prod-525025654699.australia-southeast1.run.app/?project=f-dse) | • [Local Aurora](http://uk-bh-cloudtop.c.googlers.com:9000/?project=sample)<br>• [Local Monaro](http://uk-bh-cloudtop.c.googlers.com:9000/?project=f-dse) |
| **Cloud Run Services** | [👉 Cloud Run Console (Dev)](https://pantheon.corp.google.com/run?project=monaro-risk-dev) | [👉 Cloud Run Console (Prod)](https://pantheon.corp.google.com/run?project=monaro-risk-prod) | — |
| **Cloud Build Triggers** | [👉 Build Triggers (Dev)](https://pantheon.corp.google.com/cloud-build/triggers?project=monaro-risk-dev) | [👉 Build Triggers (Prod)](https://pantheon.corp.google.com/cloud-build/triggers?project=monaro-risk-prod) | — |
| **Cloud Build History** | [👉 Build History (Dev)](https://pantheon.corp.google.com/cloud-build/builds?project=monaro-risk-dev) | [👉 Build History (Prod)](https://pantheon.corp.google.com/cloud-build/builds?project=monaro-risk-prod) | — |
| **Artifact Registry** | [👉 Docker Images (Dev)](https://pantheon.corp.google.com/artifacts?project=monaro-risk-dev) | [👉 Docker Images (Prod)](https://pantheon.corp.google.com/artifacts?project=monaro-risk-prod) | — |
| **Cloud Logging** | [👉 Logs Explorer (Dev)](https://pantheon.corp.google.com/logs/query?project=monaro-risk-dev) | [👉 Logs Explorer (Prod)](https://pantheon.corp.google.com/logs/query?project=monaro-risk-prod) | — |

- **Deployment, Provisioning & Operations**: See [`docs/DEPLOYMENT_GUIDE.md`](./docs/DEPLOYMENT_GUIDE.md) for the comprehensive canonical guide: automated CI/CD pipelines, turnkey environment provisioning (`./deploy/provision_environment.sh`), production release tag workflows, and SRE Day-2 runbooks.
- **Cloud Services, APIs & Running Costs**: See [`docs/CLOUD_COSTS_AND_API_REVIEW.md`](./docs/CLOUD_COSTS_AND_API_REVIEW.md) for an audit of all 14 GCP APIs, workload modeling for 10–50 daily users, itemized Sydney running costs (<$1.00/month), and cost optimization recommendations.

---

## 🔒 Security & Privacy

- **Strict Isolation**: Proprietary datasets (such as `data/f-dse/` or `data/local/`) and secret keys (`.env`) are excluded in `.gitignore`.
- **Zero Hardcoded Secrets**: Gemini API calls support standard Google Cloud Application Default Credentials (ADC) or environment-managed keys.

---

## 📄 License
Licensed under the Apache 2.0 License.
