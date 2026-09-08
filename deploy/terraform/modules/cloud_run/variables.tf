variable "project_id" {
  description = "Google Cloud project ID"
  type        = string
}

variable "region" {
  description = "GCP Region for Cloud Run"
  type        = string
  default     = "australia-southeast1"
}

variable "service_name" {
  description = "Name of the Cloud Run web presentation service"
  type        = string
}

variable "sync_job_name" {
  description = "Name of the Cloud Run scheduled ingestion job"
  type        = string
  default     = "monaro-risk-sync-job"
}

variable "web_image" {
  description = "Docker image for web service"
  type        = string
}

variable "sync_image" {
  description = "Docker image for sync job"
  type        = string
}

variable "service_account_email" {
  description = "Email of the deployer service account"
  type        = string
}

variable "data_bucket_name" {
  description = "Name of the GCS application persistence bucket"
  type        = string
}

variable "access_group" {
  description = "Google Group for IAP access"
  type        = string
}

variable "twosync_group" {
  description = "Twosync Google Group for IAP access"
  type        = string
  default     = ""
}

variable "lead_users" {
  description = "Lead user accounts for IAP access and job execution"
  type        = list(string)
  default     = ["brendanhills@google.com", "allins@google.com"]
}

variable "gemini_model" {
  description = "Gemini model identifier"
  type        = string
  default     = "gemini-3.5-flash"
}

variable "gemini_region" {
  description = "Vertex AI region for Gemini execution"
  type        = string
  default     = "us-central1"
}
