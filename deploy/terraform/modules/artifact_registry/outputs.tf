output "repository_id" {
  description = "ID of the Artifact Registry repository"
  value       = google_artifact_registry_repository.docker_repo.repository_id
}

output "repository_name" {
  description = "Fully qualified name of the Artifact Registry repository"
  value       = google_artifact_registry_repository.docker_repo.name
}

output "registry_url" {
  description = "Registry domain URL for Docker tags"
  value       = "${google_artifact_registry_repository.docker_repo.location}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker_repo.repository_id}"
}
