project_id        = "monaro-risk-prod"
region            = "australia-southeast1"
environment       = "prod"
github_repo_owner = "brendanhills"
github_repo_name  = "uk-bh-project-dash"
access_group      = "monaro-risk-prod@google.com"
admin_email       = "monaro-risk-prod@google.com"
notification_emails = [
  "brendanhills@google.com",
  "allins@google.com"
]
lead_users = [
  "brendanhills@google.com",
  "allins@google.com"
]
cloud_run_image = "australia-southeast1-docker.pkg.dev/monaro-risk-prod/cloud-run-source-deploy/monaro-risk-dash-prod:latest"
sync_image      = "australia-southeast1-docker.pkg.dev/monaro-risk-prod/cloud-run-source-deploy/monaro-risk-dash-prod:latest"
drive_folder_id = "1JIsbi35mXn4W-NxjbLTWo22FQMv_zv-C"
gemini_model    = "gemini-3.5-flash"
gemini_region   = "us-central1"
