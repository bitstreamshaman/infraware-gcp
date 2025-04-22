terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs
resource "google_project_service" "run_api" {
  service = "run.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "firestore_api" {
  service = "firestore.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "storage_api" {
  service = "storage.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "cloudbuild_api" {
  service = "cloudbuild.googleapis.com"
  disable_on_destroy = false
}

# Create Cloud Storage bucket for artifacts
resource "google_storage_bucket" "artifacts_bucket" {
  name     = "${var.bucket_name_prefix}-${var.project_id}"
  location = var.region
  uniform_bucket_level_access = true
  
  # Bucket configuration
  versioning {
    enabled = false
  }
  
  # Optional: Set a lifecycle rule to delete old objects
  lifecycle_rule {
    condition {
      age = 30 # days
    }
    action {
      type = "Delete"
    }
  }
  
  depends_on = [google_project_service.storage_api]
}

# Create service account for Cloud Run
resource "google_service_account" "cloud_run_service_account" {
  account_id   = "nl-to-iac-service-account"
  display_name = "NL to IaC Service Account"
}

# Grant the service account access to Cloud Storage
resource "google_storage_bucket_iam_member" "storage_admin" {
  bucket = google_storage_bucket.artifacts_bucket.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.cloud_run_service_account.email}"
}

# Grant the service account access to Firestore
resource "google_project_iam_member" "firestore_user" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.cloud_run_service_account.email}"
}

# Cloud Run service
resource "google_cloud_run_service" "nl_to_iac_api" {
  name     = var.service_name
  location = var.region
  
  template {
    spec {
      containers {
        image = var.container_image_url != "" ? var.container_image_url : "gcr.io/${var.project_id}/${var.service_name}"
        
        resources {
          limits = {
            cpu    = "1000m"
            memory = "2Gi"
          }
        }
        
        env {
          name  = "GCP_PROJECT_ID"
          value = var.project_id
        }
        
        env {
          name  = "GCP_STORAGE_BUCKET"
          value = google_storage_bucket.artifacts_bucket.name
        }
      }
      
      service_account_name = google_service_account.cloud_run_service_account.email
      
      timeout_seconds = 3600
    }
  }
  
  traffic {
    percent         = 100
    latest_revision = true
  }
  
  depends_on = [
    google_project_service.run_api,
    google_storage_bucket_iam_member.storage_admin,
    google_project_iam_member.firestore_user
  ]
  
  autogenerate_revision_name = true
}

# Make the Cloud Run service publicly accessible
resource "google_cloud_run_service_iam_member" "public_access" {
  location = google_cloud_run_service.nl_to_iac_api.location
  service  = google_cloud_run_service.nl_to_iac_api.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Create Firestore database
resource "google_app_engine_application" "app" {
  project     = var.project_id
  location_id = var.firestore_location
  database_type = "CLOUD_FIRESTORE"
  
  depends_on = [google_project_service.firestore_api]
}

