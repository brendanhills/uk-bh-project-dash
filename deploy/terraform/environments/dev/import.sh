#!/usr/bin/env bash
# ==============================================================================
# Project Monaro — Terraform Resource Import Runbook (dev)
# Safely imports existing GCP infrastructure in monaro-risk-dev into state
# without modifying or destroying running production/development resources.
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

PROJECT_ID="${1:-monaro-risk-dev}"
REGION="australia-southeast1"
SA_NAME="github-deployer"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
GAR_REPO="cloud-run-source-deploy"
SERVICE_NAME="monaro-risk-dash-dev"
SYNC_JOB_NAME="monaro-risk-sync-job"
SYNC_QUEUE_NAME="monaro-sync-queue"
SCHED_JOB_NAME="monaro-sync-schedule"
DATA_BUCKET="${PROJECT_ID}-data"
STATE_BUCKET="${PROJECT_ID}-terraform-state"

echo "=============================================================================="
echo "🏛️  Project Monaro: Terraform State Import [${PROJECT_ID}] (${REGION})"
echo "=============================================================================="

# Initialize backend
terraform init

safe_import() {
  local addr="$1"
  local id="$2"
  echo "--> Checking ${addr}..."
  if terraform state list | grep -Fxq "${addr}"; then
    echo "    Already present in state: ${addr}"
  else
    echo "    Importing ${id} -> ${addr}..."
    if terraform import "${addr}" "${id}"; then
      echo "    ✓ Successfully imported ${addr}"
    else
      echo "    ⚠️ Notice: Import failed or resource not found for ${addr}. Skipping."
    fi
  fi
}

echo "=== 1. Importing GCP Storage Buckets ==="
safe_import "module.storage.google_storage_bucket.data_bucket" "${DATA_BUCKET}"
safe_import "module.storage.google_storage_bucket.terraform_state" "${STATE_BUCKET}"

echo "=== 2. Importing Artifact Registry ==="
safe_import "module.artifact_registry.google_artifact_registry_repository.source_repo" "projects/${PROJECT_ID}/locations/${REGION}/repositories/${GAR_REPO}"

echo "=== 3. Importing Service Account & IAM ==="
safe_import "module.iam.google_service_account.deployer" "projects/${PROJECT_ID}/serviceAccounts/${SA_EMAIL}"

echo "=== 4. Importing Cloud Run Web Service & Ingestion Job ==="
safe_import "module.cloud_run.google_cloud_run_v2_service.web_service" "projects/${PROJECT_ID}/locations/${REGION}/services/${SERVICE_NAME}"
safe_import "module.cloud_run.google_cloud_run_v2_job.sync_job" "projects/${PROJECT_ID}/locations/${REGION}/jobs/${SYNC_JOB_NAME}"

echo "=== 5. Importing Ingestion Pipeline (Tasks & Scheduler) ==="
safe_import "module.ingestion_pipeline.google_cloud_tasks_queue.sync_queue" "projects/${PROJECT_ID}/locations/${REGION}/queues/${SYNC_QUEUE_NAME}"
safe_import "module.ingestion_pipeline.google_cloud_scheduler_job.sync_schedule" "projects/${PROJECT_ID}/locations/${REGION}/jobs/${SCHED_JOB_NAME}"

echo "=============================================================================="
echo "✅ State Import Completed for ${PROJECT_ID}"
echo "Run 'terraform plan' to verify configuration alignment."
echo "=============================================================================="
