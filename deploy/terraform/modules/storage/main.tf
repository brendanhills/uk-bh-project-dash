resource "google_storage_bucket" "data_bucket" {
  name                        = "${var.project_id}-data"
  project                     = var.project_id
  location                    = var.region
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true
  force_destroy               = false
}

resource "google_storage_bucket" "state_bucket" {
  name                        = "${var.project_id}-terraform-state"
  project                     = var.project_id
  location                    = var.region
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true
  force_destroy               = false

  versioning {
    enabled = true
  }
}
