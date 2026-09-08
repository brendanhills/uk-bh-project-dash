variable "project_id" {
  description = "Google Cloud project ID"
  type        = string
}

variable "region" {
  description = "GCP Region for Cloud Build trigger"
  type        = string
  default     = "australia-southeast1"
}

variable "trigger_name" {
  description = "Name of the Cloud Build trigger"
  type        = string
}

variable "description" {
  description = "Description of the Cloud Build trigger"
  type        = string
  default     = "Automated deployment trigger in Sydney"
}

variable "repo_owner" {
  description = "GitHub repository owner"
  type        = string
  default     = "brendanhills"
}

variable "repo_name" {
  description = "GitHub repository name"
  type        = string
  default     = "uk-bh-project-dash"
}

variable "branch_pattern" {
  description = "Regex pattern for Git branches to trigger builds"
  type        = string
  default     = ""
}

variable "tag_pattern" {
  description = "Regex pattern for Git tags to trigger builds"
  type        = string
  default     = ""
}

variable "build_config" {
  description = "Path to Cloud Build YAML file in repository"
  type        = string
  default     = "deploy/cloudbuild.yaml"
}

variable "included_files" {
  description = "File patterns that trigger builds"
  type        = list(string)
  default     = ["**"]
}

variable "ignored_files" {
  description = "File patterns ignored by triggers"
  type        = list(string)
  default     = ["**/*.md", "docs/**", ".agents/**", "conductor/**"]
}

variable "service_account_email" {
  description = "Service account email executing Cloud Build"
  type        = string
}

variable "substitutions" {
  description = "User substitutions passed to Cloud Build"
  type        = map(string)
  default     = {}
}
