variable "project_id" {
  description = "Google Cloud project ID"
  type        = string
}

variable "service_name" {
  description = "Service name to monitor"
  type        = string
}

variable "alert_emails" {
  description = "List of email addresses to receive alert notifications"
  type        = list(string)
  default     = ["brendanhills@google.com", "allins@google.com"]
}
