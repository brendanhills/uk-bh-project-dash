output "service_account_id" {
  description = "Unique identifier of the service account"
  value       = google_service_account.deployer.id
}

output "service_account_email" {
  description = "Email address of the deployer service account"
  value       = google_service_account.deployer.email
}

output "service_account_name" {
  description = "Fully-qualified name of the service account"
  value       = google_service_account.deployer.name
}
