output "trigger_id" {
  description = "Unique ID of the Cloud Build trigger"
  value       = google_cloudbuild_trigger.trigger.id
}

output "trigger_name" {
  description = "Name of the Cloud Build trigger"
  value       = google_cloudbuild_trigger.trigger.name
}
