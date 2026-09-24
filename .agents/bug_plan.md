# Phased Bug Implementation & Focus Cycle Roadmap

Generated: 2026-09-24  
Active Strategy: **`build-polish-harden`** (`robustness` ➔ `quality` ➔ `feature` ➔ `foundation`)  
Active Workspace Cycle Focus: **`robustness`** (🛡️ Robustness & Hardening)  

---

## 1. Executive Summary & Active Cycle Rotation

Following the resolution and verification of previous stability defects, active backlog items are organized into ordered **Focus Cycle Phases**. 

Current focus is **Phase 1 (`robustness`)**, prioritizing critical deployment stability and infrastructure state alignment before moving to quality improvements and feature expansion.

```
Cycle Phase 1: 🛡️ Robustness & Hardening (Active Cycle Focus)
   └── #123 (P1: Terraform apply 409 conflict: existing resources not imported into state)

Cycle Phase 2: 🎨 Quality & UX Polish
   └── #117 (P2: run_server.sh should display web dashboard URL clearly in terminal output)

Cycle Phase 3: ✨ Feature & Expansion
   ├── #104 (P1: Easy tool to enable user to update risks sheet(s) - In Progress)
   ├── #103 (P2: Add list of admins/owners to setup.sh --status output)
   ├── #16  (P2: Interactive Google Sheet & Drive Folder switcher with human-readable names)
   ├── #6   (P2: Make Gemini Executive Summary Prompt editable)
   ├── #9   (P2: Time Machine weekly selector chips across orange header bar)
   ├── #24  (P2: Add 'Create a Slide' button near 'Copy Synthesis')
   ├── #93  (P2: Add active execution check to prevent duplicate concurrent sync runs)
   ├── #95  (P3: Support adding and scaffolding new projects dynamically)
   └── #12  (P3: Future FR: In-Dashboard Data Entry & Risk Logging Form)

Cycle Phase 4: 🏗️ Foundation & Velocity
   └── #113 (P2: Trigger sync_drive automatically when pushing a new project config update)
```

---

## 2. Phased Focus Roadmap

### Cycle Phase 1: 🛡️ Robustness & Hardening (Active Focus)

Focus: Infrastructure deployment conflicts, resource state synchronization, and clean environment provisioning.

| ID | Pri | Focus | Component | Title | Risk | Status |
| :---: | :---: | :---: | :--- | :--- | :---: | :---: |
| **#123** | **P1** | `robustness` | `deploy/terraform/` | Terraform apply 409 conflict: existing resources not imported into state | Low | `Investigated` |

- **Root Cause (#123)**:
  Terraform dev state (`monaro-risk-dev-terraform-state/terraform/state/dev`) does not track existing GCP infrastructure, causing `terraform apply` to attempt to recreate existing Artifact Registry repository, deployer service account, and GCS buckets, failing with HTTP 409 Conflict.
- **Remediation Plan**:
  1. Add `terraform import` migration helper or declarative `import {}` blocks for `module.artifact_registry.google_artifact_registry_repository.docker_repo`, `module.iam.google_service_account.deployer`, and `module.storage.google_storage_bucket.*`.
  2. Verify with `terraform plan` that existing resources match state without 409 conflict.
  3. Document bootstrap import instructions in `deploy/terraform/README.md`.
- **Verification**: Static validation (`terraform validate`, `terraform plan`).

---

### Cycle Phase 2: 🎨 Quality & UX Polish

Focus: CLI runner ergonomics and developer onboarding experience.

| ID | Pri | Focus | Component | Title | Risk | Status |
| :---: | :---: | :---: | :--- | :--- | :---: | :---: |
| **#117** | **P2** | `quality` | `run_server.sh` | run_server.sh should display web dashboard URL clearly in terminal output | Low | `Investigated` |

- **Root Cause (#117)**:
  In `run_server.sh`, `do_run` (start/restart/--no-attach) does not print clickable web dashboard URLs (`http://localhost:9000` / `http://127.0.0.1:9000`), forcing users to manually invoke `./run_server.sh status`.
- **Remediation Plan**:
  In `run_server.sh` `do_run`, display the clickable localhost and 127.0.0.1 dashboard URLs after starting or restarting the server before attaching or when running with `--no-attach`.
- **Verification**: `bash -n run_server.sh` & `./run_server.sh status`.

---

### Cycle Phase 3: ✨ Feature & Expansion

Focus: Config editing CLI tooling and user interactivity features.

| ID | Pri | Focus | Component | Title | Risk | Status |
| :---: | :---: | :---: | :--- | :--- | :---: | :---: |
| **#104** | **P1** | `feature` | `scripts/pipeline.py` | Easy tool to enable a user to update the risks sheet(s) | Low | `In Progress` |
| **#103** | **P2** | `feature` | `setup.sh` | Add the list of admins/owners to the setup --status output | Low | `Investigated` |
| **#16** | **P2** | `feature` | `src/js/` | Interactive Google Sheet & Drive Folder switcher with human-readable names | Low | `Investigated` |
| **#6** | **P2** | `feature` | `src/js/` | Make Gemini Executive Summary Prompt editable | Low | `Investigated` |
| **#9** | **P2** | `feature` | `src/js/` | Time Machine weekly selector chips across orange header bar | Low | `Investigated` |
| **#24** | **P2** | `feature` | `src/js/` | Add 'Create a Slide' button near 'Copy Synthesis' | Low | `Investigated` |
| **#93** | **P2** | `feature` | `scripts/` | Add active execution check to prevent duplicate concurrent sync runs | Low | `Investigated` |
| **#95** | **P3** | `feature` | `scripts/` | Support adding and scaffolding new projects dynamically | Low | `Investigated` |
| **#12** | **P3** | `feature` | `src/js/` | Future FR: In-Dashboard Data Entry & Risk Logging Form | Low | `Investigated` |

---

### Cycle Phase 4: 🏗️ Foundation & Velocity

Focus: Pipeline automations and background triggers.

| ID | Pri | Focus | Component | Title | Risk | Status |
| :---: | :---: | :---: | :--- | :--- | :---: | :---: |
| **#113** | **P2** | `foundation` | `scripts/pipeline.py` | Trigger sync_drive automatically when pushing a new project config update | Low | `Investigated` |

---

## 3. Conductor Track Promotion Candidates

- **Track Candidate**: `sheet_config_manager_20260924`
  - Encompasses: **#104** (CLI Config Update Tool), **#113** (Automatic sync trigger), and **#16** (Interactive Sheet/Drive switcher).
  - Promotes user self-service configuration for multi-project risk tracking.
