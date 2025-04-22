output "service_url" {
  value       = google_cloud_run_service.nl_to_iac_api.status[0].url
  description = "The URL of the deployed NL-to-IaC API"
}

output "storage_bucket" {
  value       = google_storage_bucket.artifacts_bucket.name
  description = "The name of the storage bucket for storing generated artifacts"
}

output "service_account_email" {
  value       = google_service_account.cloud_run_service_account.email
  description = "The email of the service account used by the Cloud Run service"
}

output "deployment_instructions" {
  value = <<-EOT
    Deployment completed successfully!
    
    API URL: ${google_cloud_run_service.nl_to_iac_api.status[0].url}
    
    Before the service will work correctly, you need to:
    
    1. Build and push your container image:
       gcloud builds submit --tag gcr.io/${var.project_id}/${var.service_name}
    
    2. Test the API with:
       curl -X GET ${google_cloud_run_service.nl_to_iac_api.status[0].url}/health
    
    3. Monitor logs with:
       gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=${var.service_name}" --limit=10
  EOT
  description = "Instructions for completing the deployment"
}