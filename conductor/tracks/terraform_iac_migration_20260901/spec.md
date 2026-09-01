# Specification: Terraform Infrastructure as Code (IaC) Migration

**Track ID:** `terraform_iac_migration_20260901`  
**Type:** `Refactor / Infrastructure`  
**Status:** `Planning`  

## 1. Overview & Objectives
Transition Project Dash's GCP infrastructure from imperatively executed bash scripts (`deploy/provision_environment.sh`) into clean, reusable, declarative **Terraform modules**. This provides drift detection, previewable `terraform plan` diffs, environment parity between `dev` and `prod`, and automated state locking.

## 2. Resources in Scope for Terraform Migration
1. **Google APIs & Services (`google_project_service`)**: All 16 required GCP APIs managed declaratively with `disable_on_destroy = false`.
2. **Artifact Registry (`google_artifact_registry_repository`)**: Standard Docker repository `cloud-run-source-deploy` in Sydney (`australia-southeast1`).
3. **Service Accounts & IAM (`google_service_account`, `google_project_iam_member`)**:
   - `github-deployer` service account.
   - Least-privilege roles (`run.admin`, `artifactregistry.admin`, `storage.admin`, `iap.admin`, `logging.logWriter`, `iam.serviceAccountUser`, `containeranalysis.occurrences.editor`).
4. **Cloud Run Web Services (`google_cloud_run_v2_service`)**:
   - Static presentation services (`monaro-risk-dash-dev` / `monaro-risk-dash-prod`) with private ingress, regional routing, and IAP bindings.
5. **Cloud Run Ingestion Jobs (`google_cloud_run_v2_job`)**:
   - `monaro-risk-sync-job` executing `scripts/sync_drive.py` with `PYTHONPATH=/app` and attached service account.
6. **Cloud Tasks (`google_cloud_tasks_queue`)**:
   - `monaro-sync-queue` with max concurrency = 1, rate limits, and retry configuration.
7. **Cloud Scheduler (`google_cloud_scheduler_job`)**:
   - `monaro-sync-schedule` triggering `monaro-risk-sync-job:run` weekly on Fridays at 5:00 PM Sydney time with OAuth token authentication.
8. **Cloud Build Triggers (`google_cloudbuild_trigger`)**:
   - Continuous deployment on `dev` branch push and production tag release trigger (`^project_dash/prod-.*$`).
9. **Monitoring & Alerting (`google_monitoring_notification_channel`, `google_monitoring_alert_policy`)**:
   - Admin email notification channel and log-based alert policy for container crashes and 5xx exceptions.
10. **IAP Access Control (`google_cloud_run_v2_service_iam_member`)**:
    - User and Google Group access grants (`roles/iap.httpsResourceAccessor`, `roles/run.invoker`).

## 3. Target Module Architecture
```
deploy/terraform/
├── environments/
│   ├── dev/
│   │   ├── main.tf              # Environment instantiation for monaro-risk-dev
│   │   ├── variables.tf
│   │   ├── terraform.tfvars
│   │   └── outputs.tf
│   └── prod/
│       ├── main.tf              # Environment instantiation for monaro-risk-prod
│       ├── variables.tf
│       ├── terraform.tfvars
│       └── outputs.tf
└── modules/
    ├── apis/                    # 16 google_project_service definitions
    ├── iam/                     # Service accounts & IAM role bindings
    ├── artifact_registry/       # Docker repository in Sydney
    ├── cloud_run/               # Web service (Nginx) & Ingestion Job (Python)
    ├── ingestion_pipeline/      # Cloud Tasks queue & Cloud Scheduler cron
    ├── cloud_build/             # CI/CD build triggers
    └── monitoring/              # Error Reporting & log-based alert policies
```

## 4. Non-Functional Requirements & Safety
- **Zero-Downtime State Import**: Support importing existing live GCP resources into Terraform state using `terraform import` without destroying live services or deleting Artifact Registry images.
- **Provider & Version Locking**: Lock `hashicorp/google` provider to `>= 5.0.0` with Australian region default `australia-southeast1`.
- **Remote State Locking**: Support Cloud Storage backend (`backend "gcs"`) for multi-developer state locking.
