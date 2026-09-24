output "trigger_id" {
  description = "Unique ID of the Cloud Build trigger"
  value       = try(google_cloudbuild_trigger.trigger[0].id, "")
}

output "trigger_name" {
  description = "Name of the Cloud Build trigger"
  value       = try(google_cloudbuild_trigger.trigger[0].name, "")
}
