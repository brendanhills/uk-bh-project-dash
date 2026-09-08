variable "project_id" {
  type        = string
  description = "GCP Project ID"
  default     = "monaro-risk-prod"
}

variable "region" {
  type        = string
  description = "GCP Region"
  default     = "australia-southeast1"
}

variable "environment" {
  type        = string
  description = "Target deployment environment (dev or prod)"
  default     = "prod"
}

variable "github_repo_owner" {
  type        = string
  description = "GitHub repository owner"
  default     = "brendanhills"
}

variable "github_repo_name" {
  type        = string
  description = "GitHub repository name"
  default     = "uk-bh-project-dash"
}

variable "access_group" {
  type        = string
  description = "Viewer group for IAP and Cloud Run Invoker access"
  default     = "monaro-risk-prod@google.com"
}

variable "admin_email" {
  type        = string
  description = "Admin notification email for alerts"
  default     = "monaro-risk-prod@google.com"
}

variable "notification_emails" {
  type        = list(string)
  description = "Notification emails for monitoring alert policies"
  default     = ["brendanhills@google.com", "allins@google.com"]
}

variable "lead_users" {
  type        = list(string)
  description = "Lead users granted Cloud Run Invoker and IAP access"
  default     = ["brendanhills@google.com", "allins@google.com"]
}

variable "cloud_run_image" {
  type        = string
  description = "Container image for Cloud Run web service"
  default     = "australia-southeast1-docker.pkg.dev/monaro-risk-prod/cloud-run-source-deploy/monaro-risk-dash-prod:latest"
}

variable "sync_image" {
  type        = string
  description = "Container image for Cloud Run ingestion sync job"
  default     = "australia-southeast1-docker.pkg.dev/monaro-risk-prod/cloud-run-source-deploy/monaro-risk-dash-prod:latest"
}

variable "drive_folder_id" {
  type        = string
  description = "Google Drive folder ID for Project Monaro"
  default     = "1JIsbi35mXn4W-NxjbLTWo22FQMv_zv-C"
}

variable "gemini_model" {
  type        = string
  description = "Gemini model identifier for LLM summaries"
  default     = "gemini-3.5-flash"
}

variable "gemini_region" {
  type        = string
  description = "Vertex AI / Gemini region"
  default     = "us-central1"
}
