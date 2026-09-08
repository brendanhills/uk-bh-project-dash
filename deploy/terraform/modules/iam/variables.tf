variable "project_id" {
  description = "Google Cloud project ID"
  type        = string
}

variable "service_account_id" {
  description = "Service account ID for CI/CD deployer"
  type        = string
  default     = "github-deployer"
}

variable "deployer_roles" {
  description = "IAM roles granted to deployer service account"
  type        = list(string)
  default = [
    "roles/run.admin",
    "roles/artifactregistry.admin",
    "roles/storage.objectAdmin",
    "roles/iap.admin",
    "roles/logging.logWriter",
    "roles/iam.serviceAccountUser",
    "roles/aiplatform.user",
    "roles/containeranalysis.occurrences.editor",
    "roles/cloudtasks.enqueuer",
    "roles/run.developer",
  ]
}
