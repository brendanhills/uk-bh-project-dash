output "web_service_name" {
  description = "Name of the Cloud Run web service"
  value       = google_cloud_run_v2_service.web_service.name
}

output "web_service_uri" {
  description = "URI of the Cloud Run web service"
  value       = google_cloud_run_v2_service.web_service.uri
}

output "sync_job_name" {
  description = "Name of the Cloud Run ingestion sync job"
  value       = google_cloud_run_v2_job.sync_job.name
}
