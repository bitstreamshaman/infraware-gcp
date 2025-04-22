variable "project_id" {
  description = "The ID of the GCP project"
  type        = string
}

variable "region" {
  description = "The GCP region where resources will be created"
  type        = string
  default     = "us-central1"
}

variable "firestore_location" {
  description = "The location for Firestore database"
  type        = string
  default     = "us-central"
}

variable "service_name" {
  description = "The name of the Cloud Run service"
  type        = string
  default     = "nl-to-iac-api"
}

variable "bucket_name_prefix" {
  description = "Prefix for the Cloud Storage bucket name"
  type        = string
  default     = "nl-to-iac-artifacts"
}

variable "container_image_url" {
  description = "Optional: URL of an existing container image. If not provided, the service will use gcr.io/[project_id]/[service_name]"
  type        = string
  default     = ""
}