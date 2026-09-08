output "project_id" {
  value       = var.project_id
  description = "GCP Project ID"
}

output "web_service_url" {
  value       = module.cloud_run.web_service_uri
  description = "Cloud Run Web Service URL"
}

output "data_bucket" {
  value       = module.storage.data_bucket_name
  description = "Cloud Storage data persistence bucket"
}

output "deployer_service_account" {
  value       = module.iam.deployer_sa_email
  description = "GitHub & Cloud Build deployer service account email"
}

output "artifact_registry_repo" {
  value       = module.artifact_registry.repository_id
  description = "Artifact Registry Docker repository ID"
}
