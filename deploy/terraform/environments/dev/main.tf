terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 8.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# 1. GCP APIs
module "apis" {
  source     = "../../modules/apis"
  project_id = var.project_id
}

# 2. Cloud Storage
module "storage" {
  source     = "../../modules/storage"
  project_id = var.project_id
  region     = var.region

  depends_on = [module.apis]
}

# 3. Artifact Registry
module "artifact_registry" {
  source     = "../../modules/artifact_registry"
  project_id = var.project_id
  region     = var.region

  depends_on = [module.apis]
}

# 4. IAM & Service Accounts
module "iam" {
  source     = "../../modules/iam"
  project_id = var.project_id

  depends_on = [module.apis]
}

# 5. Cloud Run Web Service & Ingestion Job
module "cloud_run" {
  source                = "../../modules/cloud_run"
  project_id            = var.project_id
  region                = var.region
  service_name          = "monaro-risk-dash-${var.environment}"
  sync_job_name         = "monaro-risk-sync-job"
  web_image             = var.cloud_run_image
  sync_image            = var.sync_image
  data_bucket_name      = module.storage.data_bucket_name
  service_account_email = module.iam.deployer_sa_email
  access_group          = var.access_group
  lead_users            = var.lead_users
  gemini_model          = var.gemini_model
  gemini_region         = var.gemini_region

  depends_on = [
    module.apis,
    module.storage,
    module.iam
  ]
}

# 6. Ingestion Pipeline (Cloud Tasks & Cloud Scheduler)
module "ingestion_pipeline" {
  source                = "../../modules/ingestion_pipeline"
  project_id            = var.project_id
  region                = var.region
  sync_job_name         = module.cloud_run.sync_job_name
  service_account_email = module.iam.deployer_sa_email

  depends_on = [
    module.apis,
    module.cloud_run,
    module.iam
  ]
}

# 7. Cloud Build Triggers
module "cloud_build" {
  source                = "../../modules/cloud_build"
  project_id            = var.project_id
  region                = var.region
  trigger_name          = "deploy-monaro-risk-dash-${var.environment}"
  service_account_email = module.iam.deployer_sa_email
  repo_owner            = var.github_repo_owner
  repo_name             = var.github_repo_name
  branch_pattern        = "^main$"
  tag_pattern           = ""

  depends_on = [
    module.apis,
    module.iam
  ]
}

# 8. Cloud Monitoring & Alerts
module "monitoring" {
  source       = "../../modules/monitoring"
  project_id   = var.project_id
  service_name = module.cloud_run.web_service_name
  alert_emails = var.notification_emails

  depends_on = [module.apis]
}
