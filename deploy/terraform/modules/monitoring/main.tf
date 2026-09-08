resource "google_monitoring_notification_channel" "email" {
  for_each     = toset(var.alert_emails)
  project      = var.project_id
  display_name = "Admin Alert Email (${each.key})"
  type         = "email"

  labels = {
    email_address = each.key
  }
}

resource "google_monitoring_alert_policy" "error_alerts" {
  project      = var.project_id
  display_name = "${var.service_name} Container Crash & Error Alert"
  combiner     = "OR"

  conditions {
    display_name = "Cloud Run Severity Error or 5xx"
    condition_matched_log {
      filter = "resource.type=\"cloud_run_revision\" AND (severity>=ERROR OR jsonPayload.status>=500)"
    }
  }

  notification_channels = [for ch in google_monitoring_notification_channel.email : ch.name]

  alert_strategy {
    auto_close = "1800s"
    notification_rate_limit {
      period = "300s"
    }
  }
}
