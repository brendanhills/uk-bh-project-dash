# ==============================================================================
# Declarative Terraform 1.5+ Import Blocks for dev (monaro-risk-dev)
#
# When applying against an environment with pre-existing GCP resources,
# these import blocks instruct Terraform to automatically bind existing
# infrastructure into state during 'terraform plan' / 'terraform apply',
# preventing HTTP 409 Conflict (already exists) errors.
# ==============================================================================

# 1. Cloud Storage Buckets
import {
  to = module.storage.google_storage_bucket.data_bucket
  id = "monaro-risk-dev-data"
}

import {
  to = module.storage.google_storage_bucket.state_bucket
  id = "monaro-risk-dev-terraform-state"
}

# 2. Artifact Registry Docker Repository
import {
  to = module.artifact_registry.google_artifact_registry_repository.docker_repo
  id = "projects/monaro-risk-dev/locations/australia-southeast1/repositories/cloud-run-source-deploy"
}

# 3. GitHub / Deployer Service Account
import {
  to = module.iam.google_service_account.deployer
  id = "projects/monaro-risk-dev/serviceAccounts/github-deployer@monaro-risk-dev.iam.gserviceaccount.com"
}

# 4. Cloud Run Web Service & Ingestion Sync Job
import {
  to = module.cloud_run.google_cloud_run_v2_service.web_service
  id = "projects/monaro-risk-dev/locations/australia-southeast1/services/monaro-risk-dash-dev"
}

import {
  to = module.cloud_run.google_cloud_run_v2_job.sync_job
  id = "projects/monaro-risk-dev/locations/australia-southeast1/jobs/monaro-risk-sync-job"
}

# 5. Ingestion Pipeline: Cloud Tasks Queue & Cloud Scheduler Job
import {
  to = module.ingestion_pipeline.google_cloud_tasks_queue.sync_queue
  id = "projects/monaro-risk-dev/locations/australia-southeast1/queues/monaro-sync-queue"
}

import {
  to = module.ingestion_pipeline.google_cloud_scheduler_job.sync_schedule
  id = "projects/monaro-risk-dev/locations/australia-southeast1/jobs/monaro-sync-schedule"
}
