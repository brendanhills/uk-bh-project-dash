terraform {
  backend "gcs" {
    bucket = "monaro-risk-dev-terraform-state"
    prefix = "terraform/state/dev"
  }
}
