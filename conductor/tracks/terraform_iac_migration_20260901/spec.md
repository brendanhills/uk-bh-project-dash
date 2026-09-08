# Specification: Terraform Infrastructure as Code (IaC) Migration

**Track ID:** `terraform_iac_migration_20260901`  
**Type:** `Refactor / Infrastructure`  
**Status:** `Planning`  

## 1. Overview & Objectives
Transition Project Dash's GCP infrastructure from complex imperative shell scripts into clean, reusable, declarative **Terraform modules** backed by a streamlined root pre-flight bootstrap helper ([`setup.sh`](file:///usr/local/google/home/brendanhills/dev/apps/project_dash/setup.sh)). This codifies all infrastructure in Sydney (`australia-southeast1`), synchronizes with the active GitHub repository (`brendanhills/uk-bh-project-dash`), provides drift detection, previewable `terraform plan` diffs, environment parity between `dev` and `prod`, and automated remote state locking in GCS.

## 2. Resources in Scope for Terraform Migration
1. **Google APIs & Services (`google_project_service`)**:
   - All 16 required GCP APIs declared in `modules/apis` with `disable_on_destroy = false`.
2. **Cloud Storage Buckets (`google_storage_bucket`)**:
   - Application data persistence bucket (`${PROJECT_ID}-data`) in Sydney (`australia-southeast1`) with uniform bucket-level access and standard storage class, mounted by Cloud Run services and jobs.
   - Remote Terraform state bucket (`${PROJECT_ID}-terraform-state`) with uniform bucket-level access and object versioning enabled.
3. **Artifact Registry (`google_artifact_registry_repository`)**:
   - Docker repository `cloud-run-source-deploy` in Sydney (`australia-southeast1`).
   - Native declarative `cleanup_policies` block matching `cleanup-policy.json` (retaining last 10 versions and deleting untagged images older than 14 days).
4. **Service Accounts & IAM (`google_service_account`, `google_project_iam_member`)**:
   - `github-deployer` service account (`github-deployer@${PROJECT_ID}.iam.gserviceaccount.com`).
   - Project-level least-privilege role bindings: `roles/run.admin`, `roles/artifactregistry.admin`, `roles/storage.objectAdmin`, `roles/iap.admin`, `roles/logging.logWriter`, `roles/iam.serviceAccountUser`, `roles/aiplatform.user`, `roles/containeranalysis.occurrences.editor`, `roles/cloudtasks.enqueuer`, `roles/run.developer`.
5. **Cloud Run Web Services (`google_cloud_run_v2_service`)**:
   - Regional presentation services (`monaro-risk-dash-dev` / `monaro-risk-dash-prod`) in `australia-southeast1`.
   - Private ingress (`--no-allow-unauthenticated`), port 8080, Gen2 execution environment, and GCS volume mount to `${PROJECT_ID}-data` at `/app/data`.
6. **Cloud Run Ingestion Jobs (`google_cloud_run_v2_job`)**:
   - Scheduled ingestion job `monaro-risk-sync-job` executing `python,scripts/sync_drive.py` with arguments `--project=monaro`.
   - Gen2 execution environment, GCS volume mount to `${PROJECT_ID}-data` at `/app/data`, and environment variables (`DEFAULT_PROJECTS=monaro`, `GEMINI_MODEL=gemini-3.5-flash`, `GEMINI_REGION=us-central1`).
7. **Cloud Tasks Queues (`google_cloud_tasks_queue`)**:
   - Regional queue `monaro-sync-queue` in Sydney with `max_concurrent_dispatches = 1`, `max_attempts = 3`.
8. **Cloud Scheduler Crons (`google_cloud_scheduler_job`)**:
   - Cron `monaro-sync-schedule` triggering `monaro-risk-sync-job:run` weekly on Fridays at 17:00 Sydney time (`0 17 * * 5`, `Australia/Sydney`) via HTTP POST authenticated with OAuth service account tokens.
9. **Cloud Build Triggers (`google_cloudbuild_trigger`)**:
   - Connected to GitHub repository `brendanhills/uk-bh-project-dash`.
   - **Dev Trigger:** Push to branch `main` watching `**` (ignoring `**/*.md`, `docs/**`, `conductor/**`, `.agents/**`), executing `deploy/cloudbuild.yaml` with substitutions for `monaro-risk-dash-dev`.
   - **Prod Trigger:** Release tag matching `^project_dash/prod-.*$` (or `^prod-.*$`), executing `deploy/cloudbuild.yaml` with substitutions for `monaro-risk-dash-prod`.
10. **Monitoring & Alerting (`google_monitoring_notification_channel`, `google_monitoring_alert_policy`)**:
    - Email notification channels for leads (`brendanhills@google.com`, `allins@google.com`).
    - Log-based alert policy for container crashes, unhandled 5xx errors, and pipeline failures.
11. **Identity-Aware Proxy (IAP) & Invoker Access (`google_cloud_run_v2_service_iam_member`, `google_iap_web_iam_member`)**:
    - `roles/iap.httpsResourceAccessor` and `roles/run.invoker` granted to:
      - Groups: `monaro-risk-dev@google.com` / `monaro-risk-dev@twosync.google.com` (Dev) and `monaro-risk-prod@google.com` / `monaro-risk-prod@twosync.google.com` (Prod).
      - Lead Users: `brendanhills@google.com`, `allins@google.com`.
12. **Manual Checkpoints Auditing (`setup.sh --status`)**:
    - `setup.sh --status` actively detects and clearly reports the status of all manual prerequisite steps:
      1. GitHub Repository Connection in Cloud Build (`CONNECTED` vs `OUTSTANDING`)
      2. OAuth Consent Screen & Brand for IAP (`CONFIGURED` vs `OUTSTANDING`)
      3. Google Drive Shared Folder Access (`VERIFIED` vs `OUTSTANDING`)
      4. Permanent Billing Account Attachment (`ATTACHED` vs `SANDBOX (EXP: 15-NOV-2026)`)
      5. Google Groups / Access Rosters (`ACTIVE` vs `OUTSTANDING`)

## 3. Target Module Architecture
```
setup.sh                         # Root developer cockpit: sub-5s parallel health audit (--status, -l, -m), bootstrap, and TF delegator
deploy/
└── terraform/
    ├── environments/
    │   ├── dev/
    │   │   ├── main.tf          # Environment composition for monaro-risk-dev
    │   │   ├── variables.tf
    │   │   ├── terraform.tfvars # Dev project ID, Sydney region, dev Google group
    │   │   ├── backend.tf       # GCS backend configuration (monaro-risk-dev-terraform-state)
    │   │   └── outputs.tf
    │   └── prod/
    │       ├── main.tf          # Environment composition for monaro-risk-prod
    │       ├── variables.tf
    │       ├── terraform.tfvars # Prod project ID, Sydney region, prod Google group
    │       ├── backend.tf       # GCS backend configuration (monaro-risk-prod-terraform-state)
    │       └── outputs.tf
    └── modules/
        ├── apis/                # 16 google_project_service definitions
        ├── storage/             # GCS persistence bucket (${PROJECT_ID}-data) & state bucket
        ├── iam/                 # Service account & least-privilege IAM role bindings
        ├── artifact_registry/   # Docker repository with native cleanup policies
        ├── cloud_run/           # Web service (Nginx) & Ingestion Job (Python) with GCS mounts
        ├── ingestion_pipeline/  # Cloud Tasks queue & Cloud Scheduler cron
        ├── cloud_build/         # CI/CD GitHub triggers for main branch and prod tags
        └── monitoring/          # Error Reporting notification channels & alert policies
```

## 4. Non-Functional Requirements & Safety
- **Zero-Downtime State Import**: Support importing existing live GCP resources into Terraform state using `terraform import` without destroying live services or deleting Artifact Registry images.
- **Provider & Version Locking**: Lock `hashicorp/google` provider to `>= 5.0.0` with Australian region default `australia-southeast1`.
- **Remote State Locking**: Cloud Storage backend (`backend "gcs"`) with object versioning for state audit and collision prevention.
- **Preserve Fast Status Audit (`setup.sh --status`)**: Retain the high-speed parallel audit engine in root `setup.sh` (`--status`, `-l`, `-m`, `--state-only`) providing sub-5s visibility into all 46 tracked GCP and Google Drive assets without requiring Terraform state locks.
- **Manual Checkpoint Transparency**: `setup.sh --status` must clearly display a dedicated section for manual/interactive checkpoints (GitHub connection, OAuth screen, Drive access, Billing, Google Groups) showing which are **COMPLETE (`[✓]`)** vs **OUTSTANDING (`[!]`)**, including direct 1-click Pantheon URLs for any action required.
- **Root Developer Cockpit**: Refactor root `setup.sh` so that provisioning delegates directly to Terraform (`terraform apply`), while preserving `--status` inspection and pre-flight bootstrap.
- **Test Integrity**: Ensure `tests/test_frontend_contracts.py` continues to pass syntax and option assertions for `setup.sh`.
