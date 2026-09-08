variable "project_id" {
  description = "Google Cloud project ID"
  type        = string
}

variable "region" {
  description = "GCP Region for Artifact Registry repository"
  type        = string
  default     = "australia-southeast1"
}

variable "repository_id" {
  description = "Artifact Registry Docker repository ID"
  type        = string
  default     = "cloud-run-source-deploy"
}
