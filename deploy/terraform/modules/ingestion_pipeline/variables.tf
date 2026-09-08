variable "project_id" {
  description = "Google Cloud project ID"
  type        = string
}

variable "region" {
  description = "GCP Region for Cloud Tasks and Cloud Scheduler"
  type        = string
  default     = "australia-southeast1"
}

variable "queue_name" {
  description = "Name of the Cloud Tasks queue"
  type        = string
  default     = "monaro-sync-queue"
}

variable "scheduler_job_name" {
  description = "Name of the Cloud Scheduler job"
  type        = string
  default     = "monaro-sync-schedule"
}

variable "sync_job_name" {
  description = "Target Cloud Run sync job name"
  type        = string
  default     = "monaro-risk-sync-job"
}

variable "service_account_email" {
  description = "Service account email for OAuth authentication"
  type        = string
}

variable "schedule_cron" {
  description = "Cron expression for automated weekly ingestion"
  type        = string
  default     = "0 17 * * 5"
}

variable "time_zone" {
  description = "Time zone for Cloud Scheduler"
  type        = string
  default     = "Australia/Sydney"
}
