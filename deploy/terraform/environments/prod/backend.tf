terraform {
  backend "gcs" {
    bucket = "monaro-risk-prod-terraform-state"
    prefix = "terraform/state/prod"
  }
}
