data "google_project" "current" {
  project_id = var.project_id
}

locals {
  viewer_members = concat(
    [for g in [var.access_group, var.twosync_group] : "group:${g}" if g != ""],
    [for u in var.lead_users : "user:${u}"]
  )
}

# 1. Cloud Run Web Presentation Service
resource "google_cloud_run_v2_service" "web_service" {
  project  = var.project_id
  location = var.region
  name     = var.service_name
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    execution_environment = "EXECUTION_ENVIRONMENT_GEN2"
    service_account       = var.service_account_email

    containers {
      image = var.web_image

      ports {
        container_port = 8080
      }

      volume_mounts {
        name       = "data-volume"
        mount_path = "/app/data"
      }

      env {
        name  = "DEFAULT_PROJECTS"
        value = "monaro"
      }
      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "GCP_REGION"
        value = var.region
      }
      env {
        name  = "GEMINI_MODEL"
        value = var.gemini_model
      }
      env {
        name  = "GEMINI_REGION"
        value = var.gemini_region
      }
    }

    volumes {
      name = "data-volume"
      gcs {
        bucket    = var.data_bucket_name
        read_only = false
      }
    }
  }
}

# 2. Cloud Run Service Invoker Bindings
resource "google_cloud_run_v2_service_iam_member" "iap_agent_invoker" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.web_service.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:service-${data.google_project.current.number}@gcp-sa-iap.iam.gserviceaccount.com"
}

resource "google_cloud_run_v2_service_iam_member" "viewers_invoker" {
  for_each = toset(local.viewer_members)
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.web_service.name
  role     = "roles/run.invoker"
  member   = each.key
}

# 3. Cloud Run Ingestion Sync Job
resource "google_cloud_run_v2_job" "sync_job" {
  project  = var.project_id
  location = var.region
  name     = var.sync_job_name

  template {
    task_count = 1

    template {
      max_retries           = 1
      execution_environment = "EXECUTION_ENVIRONMENT_GEN2"
      service_account       = var.service_account_email

      containers {
        image   = var.sync_image
        command = ["python", "scripts/sync_drive.py"]
        args    = ["--project=monaro"]

        volume_mounts {
          name       = "data-volume"
          mount_path = "/app/data"
        }

        env {
          name  = "DEFAULT_PROJECTS"
          value = "monaro"
        }
        env {
          name  = "GCP_PROJECT_ID"
          value = var.project_id
        }
        env {
          name  = "GCP_REGION"
          value = var.region
        }
        env {
          name  = "GEMINI_MODEL"
          value = var.gemini_model
        }
        env {
          name  = "GEMINI_REGION"
          value = var.gemini_region
        }
      }

      volumes {
        name = "data-volume"
        gcs {
          bucket    = var.data_bucket_name
          read_only = false
        }
      }
    }
  }
}

# 4. Job IAM Bindings
resource "google_cloud_run_v2_job_iam_member" "job_invoker_sa" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_job.sync_job.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${var.service_account_email}"
}

resource "google_cloud_run_v2_job_iam_member" "job_developer_users" {
  for_each = toset([for u in var.lead_users : "user:${u}"])
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_job.sync_job.name
  role     = "roles/run.developer"
  member   = each.key
}
