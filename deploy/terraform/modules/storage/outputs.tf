output "data_bucket_name" {
  description = "Name of the application data persistence bucket"
  value       = google_storage_bucket.data_bucket.name
}

output "data_bucket_url" {
  description = "URL of the application data persistence bucket"
  value       = google_storage_bucket.data_bucket.url
}

output "state_bucket_name" {
  description = "Name of the remote Terraform state bucket"
  value       = google_storage_bucket.state_bucket.name
}
