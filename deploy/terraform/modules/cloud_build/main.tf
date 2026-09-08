resource "google_cloudbuild_trigger" "trigger" {
  project     = var.project_id
  location    = var.region
  name        = var.trigger_name
  description = var.description

  filename       = var.build_config
  included_files = var.included_files
  ignored_files  = var.ignored_files

  service_account = "projects/${var.project_id}/serviceAccounts/${var.service_account_email}"

  github {
    owner = var.repo_owner
    name  = var.repo_name

    dynamic "push" {
      for_each = var.branch_pattern != "" ? [1] : []
      content {
        branch = var.branch_pattern
      }
    }

    dynamic "push" {
      for_each = var.tag_pattern != "" ? [1] : []
      content {
        tag = var.tag_pattern
      }
    }
  }

  substitutions = var.substitutions
}
