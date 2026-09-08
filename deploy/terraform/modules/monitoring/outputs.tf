output "alert_policy_id" {
  description = "Unique ID of the alert policy"
  value       = google_monitoring_alert_policy.error_alerts.id
}

output "notification_channel_ids" {
  description = "IDs of the notification channels"
  value       = [for ch in google_monitoring_notification_channel.email : ch.id]
}
