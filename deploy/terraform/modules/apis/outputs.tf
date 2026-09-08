output "enabled_services" {
  description = "List of services managed and enabled"
  value       = [for s in google_project_service.apis : s.service]
}
