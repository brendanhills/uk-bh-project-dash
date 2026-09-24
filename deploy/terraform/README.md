# Project Monaro — Terraform Infrastructure & State Management

This directory contains Terraform Infrastructure-as-Code (IaC) definitions for Project Monaro across modular environments (`dev` and `prod`).

---

## 1. Directory Structure

```
deploy/terraform/
├── environments/
│   ├── dev/                  # Development environment (monaro-risk-dev)
│   │   ├── backend.tf        # GCS remote state configuration
│   │   ├── import.sh         # Idempotent state import runbook
│   │   ├── main.tf           # Root module orchestrator
│   │   ├── outputs.tf        # Environment outputs
│   │   ├── terraform.tfvars  # Environment variable assignments
│   │   └── variables.tf      # Variable declarations
│   └── prod/                 # Production environment (monaro-risk-prod)
│       ├── backend.tf
│       ├── main.tf
│       ├── outputs.tf
│       ├── terraform.tfvars
│       └── variables.tf
└── modules/                  # Reusable Terraform modules
    ├── apis/                 # Google Cloud Services API activation
    ├── artifact_registry/    # Docker repository & lifecycle cleanup policies
    ├── cloud_build/          # GitHub trigger & build integration
    ├── cloud_run/            # Web dashboard service & sync jobs
    ├── iam/                  # Deployer service accounts and role bindings
    ├── ingestion_pipeline/   # Cloud Tasks queues & Cloud Scheduler
    ├── monitoring/           # Cloud Monitoring alerts & uptime checks
    └── storage/              # State and data GCS buckets
```

---

## 2. Resolving 409 Conflict: Importing Pre-Existing GCP Resources

When provisioning an environment where GCP resources already exist (e.g. Artifact Registry repositories, service accounts, or GCS buckets created by manual bootstrap or previous deployment pipelines), running `terraform apply` directly against an uninitialized or fresh state bucket may fail with HTTP `409 Conflict` (resource already exists).

### Automated Idempotent Import Script

To synchronize remote GCP infrastructure with your Terraform state:

```bash
cd deploy/terraform/environments/dev
chmod +x import.sh
./import.sh [PROJECT_ID]
```

The `import.sh` script checks Terraform state first (`terraform state list`) and safely imports missing resources without overwriting or modifying active workloads:
- **Cloud Storage**: `module.storage.google_storage_bucket.data_bucket`, `module.storage.google_storage_bucket.state_bucket`
- **Artifact Registry**: `module.artifact_registry.google_artifact_registry_repository.docker_repo`
- **Service Account**: `module.iam.google_service_account.deployer`
- **Cloud Run**: `module.cloud_run.google_cloud_run_v2_service.web_service`, `module.cloud_run.google_cloud_run_v2_job.sync_job`
- **Ingestion Pipeline**: `module.ingestion_pipeline.google_cloud_tasks_queue.sync_queue`, `module.ingestion_pipeline.google_cloud_scheduler_job.sync_schedule`

---

## 3. Manual Import Reference

If you prefer importing individual resources manually using Terraform CLI:

```bash
# 1. Cloud Storage Buckets
terraform import module.storage.google_storage_bucket.data_bucket <PROJECT_ID>-data
terraform import module.storage.google_storage_bucket.state_bucket <PROJECT_ID>-terraform-state

# 2. Artifact Registry
terraform import module.artifact_registry.google_artifact_registry_repository.docker_repo \
  projects/<PROJECT_ID>/locations/<REGION>/repositories/cloud-run-source-deploy

# 3. Deployer Service Account
terraform import module.iam.google_service_account.deployer \
  projects/<PROJECT_ID>/serviceAccounts/github-deployer@<PROJECT_ID>.iam.gserviceaccount.com

# 4. Cloud Run Web Service & Sync Job
terraform import module.cloud_run.google_cloud_run_v2_service.web_service \
  projects/<PROJECT_ID>/locations/<REGION>/services/monaro-risk-dash-<ENV>

terraform import module.cloud_run.google_cloud_run_v2_job.sync_job \
  projects/<PROJECT_ID>/locations/<REGION>/jobs/monaro-risk-sync-job

# 5. Cloud Tasks & Cloud Scheduler
terraform import module.ingestion_pipeline.google_cloud_tasks_queue.sync_queue \
  projects/<PROJECT_ID>/locations/<REGION>/queues/monaro-sync-queue

terraform import module.ingestion_pipeline.google_cloud_scheduler_job.sync_schedule \
  projects/<PROJECT_ID>/locations/<REGION>/jobs/monaro-sync-schedule
```

---

## 4. Verification

After running the import runbook, execute a dry-run plan to verify 0 unexpected changes:

```bash
terraform plan
```
