variable "project_id" {
  description = "Google Cloud project ID"
  type        = string
}

variable "region" {
  description = "GCP Region for Cloud Storage buckets"
  type        = string
  default     = "australia-southeast1"
}
