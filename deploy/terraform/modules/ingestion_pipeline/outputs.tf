output "queue_id" {
  description = "ID of the Cloud Tasks queue"
  value       = google_cloud_tasks_queue.sync_queue.id
}

output "scheduler_job_id" {
  description = "ID of the Cloud Scheduler job"
  value       = google_cloud_scheduler_job.sync_schedule.id
}
