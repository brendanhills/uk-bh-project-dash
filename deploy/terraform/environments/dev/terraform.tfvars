project_id        = "monaro-risk-dev"
region            = "australia-southeast1"
environment       = "dev"
github_repo_owner = "brendanhills"
github_repo_name  = "uk-bh-project-dash"
access_group      = "monaro-risk-dev@google.com"
admin_email       = "monaro-risk-dev@google.com"
notification_emails = [
  "brendanhills@google.com",
  "allins@google.com"
]
lead_users = [
  "brendanhills@google.com",
  "allins@google.com"
]
cloud_run_image = "australia-southeast1-docker.pkg.dev/monaro-risk-dev/cloud-run-source-deploy/monaro-risk-dash-dev:latest"
sync_image      = "australia-southeast1-docker.pkg.dev/monaro-risk-dev/cloud-run-source-deploy/monaro-risk-dash-dev:latest"
drive_folder_id = "1JIsbi35mXn4W-NxjbLTWo22FQMv_zv-C"
gemini_model    = "gemini-3.5-flash"
gemini_region   = "us-central1"
