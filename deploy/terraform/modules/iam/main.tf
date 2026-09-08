resource "google_service_account" "deployer" {
  project      = var.project_id
  account_id   = var.service_account_id
  display_name = "GitHub & Cloud Build Deployer"
}

resource "google_project_iam_member" "deployer_roles" {
  for_each = toset(var.deployer_roles)
  project  = var.project_id
  role     = each.key
  member   = "serviceAccount:${google_service_account.deployer.email}"
}
