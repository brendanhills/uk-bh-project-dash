# 1. Cloud Tasks Queue for asynchronous job throttling & retries
resource "google_cloud_tasks_queue" "sync_queue" {
  project  = var.project_id
  location = var.region
  name     = var.queue_name

  rate_limits {
    max_concurrent_dispatches = 1
  }

  retry_config {
    max_attempts = 3
  }
}

# 2. Cloud Scheduler Job for weekly automated ingestion
resource "google_cloud_scheduler_job" "sync_schedule" {
  project     = var.project_id
  region      = var.region
  name        = var.scheduler_job_name
  description = "Weekly automated ingestion sync for Project Monaro"
  schedule    = var.schedule_cron
  time_zone   = var.time_zone

  http_target {
    uri         = "https://${var.region}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${var.project_id}/jobs/${var.sync_job_name}:run"
    http_method = "POST"

    oauth_token {
      service_account_email = var.service_account_email
    }
  }
}
