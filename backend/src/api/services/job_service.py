from typing import Dict, Any, Optional
from ..models.api import JobStatus
from datetime import datetime
import logging
import asyncio
import tempfile
import os
from google.auth.credentials import AnonymousCredentials
from google.cloud import firestore
from .storage_service import StorageService, get_storage_service
from .crewai_service import CrewAIService

logger = logging.getLogger(__name__)

class JobService:
    """Service for managing job processing and status using Firestore"""

    def __init__(self, storage_service: StorageService = None, crewai_service: CrewAIService = None):
        """Initialize the job service with a Firestore client and CrewAI service"""
        if os.environ.get("FIRESTORE_EMULATOR_HOST"):
            self.db = firestore.Client(
                project="local-development",
                credentials=AnonymousCredentials()
            )
        else:
            self.db = firestore.Client()

        self.jobs_collection = self.db.collection('jobs')
        self.storage_service = storage_service or get_storage_service()
        self.crewai_service = crewai_service or CrewAIService()
        self.temp_dir = tempfile.gettempdir()

    async def create_job(self, job_data: Dict[str, Any]) -> str:
        """Create a new job and store it in Firestore"""
        job_id = job_data["job_id"]
        
        # Store job in Firestore
        doc_ref = self.jobs_collection.document(job_id)
        doc_ref.set(job_data)
        
        return job_id
    
    async def update_job(self, job_id: str, updates: Dict[str, Any]) -> bool:
        """Update job data in Firestore"""
        doc_ref = self.jobs_collection.document(job_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            return False
        
        doc_ref.update(updates)
        return True
    
    async def process_job(self, job_id: str, prompt: str, cloud_provider: str, project_name: str):
        """
        Process a job asynchronously using CrewAIService for YAML and diagram generation.
        """
        try:
            # Update job status to processing
            await self.update_job(job_id, {
                "status": JobStatus.PROCESSING,
                "current_step": "Generating YAML & Diagrams",
                "updated_at": datetime.utcnow(),
                "progress": 10
            })

            # Generate YAML and diagrams using CrewAIService
            result = self.crewai_service.generate_yaml_and_diagram(job_id, prompt, cloud_provider, project_name)

            # Store YAML in Cloud Storage
            yaml_url = await self.storage_service.store_text(job_id, "yaml/infrastructure.yaml", result["yaml"])

            # Retrieve diagram URLs (assumes diagrams are saved in storage)
            diagram_urls = await self.storage_service.get_diagram_urls(job_id)

            # Update job status to diagrams ready
            await self.update_job(job_id, {
                "status": JobStatus.DIAGRAMS_READY,
                "current_step": "Waiting for user confirmation",
                "yaml_url": yaml_url,
                "diagram_urls": diagram_urls,
                "updated_at": datetime.utcnow(),
                "progress": 70,
                "message": "Diagrams are ready for review"
            })

        except Exception as e:
            logger.error(f"Error processing job {job_id}: {str(e)}", exc_info=True)
            await self.update_job(job_id, {
                "status": JobStatus.FAILED,
                "updated_at": datetime.utcnow(),
                "error": str(e),
                "message": "CrewAI diagram generation failed"
            })

    async def generate_terraform(self, job_id: str):
        """
        Generate Terraform files and documentation using CrewAIService.
        """
        try:
            # Retrieve job details
            job = await self.get_job(job_id)

            # Generate Terraform and documentation using CrewAIService
            result = self.crewai_service.generate_iac_and_docs(job_id, job["yaml_content"])

            # Retrieve Terraform file URLs
            tf_urls = await self.storage_service.get_terraform_urls(job_id)

            # Store documentation in Cloud Storage
            doc_url = await self.storage_service.store_text(job_id, "docs/documentation.md", result["docs_content"])

            # Update job status to completed
            await self.update_job(job_id, {
                "status": JobStatus.COMPLETED,
                "terraform_urls": tf_urls,
                "docs_url": doc_url,
                "updated_at": datetime.utcnow(),
                "progress": 100,
                "current_step": "IaC generation complete",
                "message": "Infrastructure as Code generation complete"
            })

        except Exception as e:
            logger.error(f"Error generating Terraform for job {job_id}: {str(e)}", exc_info=True)
            await self.update_job(job_id, {
                "status": JobStatus.FAILED,
                "updated_at": datetime.utcnow(),
                "error": str(e),
                "message": "Terraform/docs generation failed"
            })
    
    def _generate_sample_yaml(self, prompt: str, cloud_provider: str, project_name: str) -> str:
        """Generate sample YAML based on the prompt (placeholder)"""
        # This would be replaced with actual CrewAI integration
        return f"""
resources:
  - name: {project_name}-vpc
    type: vpc
    properties:
      cidr: 10.0.0.0/16
      
  - name: {project_name}-subnet
    type: subnet
    properties:
      vpc: {project_name}-vpc
      cidr: 10.0.1.0/24
      
  - name: {project_name}-vm
    type: compute_instance
    properties:
      machine_type: e2-medium
      zone: us-central1-a
      
# Generated from prompt: {prompt}
# Target cloud provider: {cloud_provider}
"""

    async def _generate_sample_diagrams(self, job_id: str, job_dir: str, project_name: str) -> list:
        """Generate sample diagrams (placeholder)"""
        # Create diagrams directory
        diagrams_dir = os.path.join(job_dir, "diagrams")
        os.makedirs(diagrams_dir, exist_ok=True)

        # Create a simple placeholder diagram
        diagram_content = f"""
    <svg width="400" height="200" xmlns="http://www.w3.org/2000/svg">
      <rect width="100%" height="100%" fill="#f0f0f0" />
      <text x="50%" y="50%" text-anchor="middle" dominant-baseline="middle" font-family="Arial" font-size="16">
        {project_name} Architecture Diagram
      </text>
    </svg>
        """.encode('utf-8')

        # Write diagram file
        diagram_path = os.path.join(diagrams_dir, "architecture.svg")
        with open(diagram_path, "wb") as f:
            f.write(diagram_content)

        # Upload to storage
        diagram_url = await self.storage_service.store_file(
            job_id,
            "diagrams/architecture.svg",
            diagram_content
        )

        return [
            {
                "name": "Architecture Diagram",
                "url": diagram_url,
                "type": "image/svg+xml"
            }
        ]

    async def _generate_sample_terraform(self, job_id: str, job_dir: str) -> list:
        """Generate sample Terraform files (placeholder)"""
        # This would be replaced with actual Terraform generation
        
        # Create Terraform directory
        tf_dir = os.path.join(job_dir, "terraform")
        os.makedirs(tf_dir, exist_ok=True)
        
        # Sample Terraform files
        terraform_files = {
            "main.tf": " You still have to implement terraform generation."        }
        
        # Write files and upload to Cloud Storage
        tf_urls = []
        for filename, content in terraform_files.items():
            file_path = os.path.join(tf_dir, filename)
            
            with open(file_path, "w") as f:
                f.write(content)
                
            # Upload to Cloud Storage
            url = await self.storage_service.store_text(
                job_id,
                f"terraform/{filename}",
                content
            )
            
            tf_urls.append({
                "name": filename,
                "url": url,
                "type": "text/plain"
            })
            
        return tf_urls
        
    async def _generate_sample_docs(self, job_id: str, job_dir: str) -> str:
        """Generate sample documentation (placeholder)"""
        # This would be replaced with actual documentation generation
        
        # Create docs directory
        docs_dir = os.path.join(job_dir, "docs")
        os.makedirs(docs_dir, exist_ok=True)
        
        # Sample documentation
        docs_content = "You still have to implement docs generation "
        
        # Write file
        docs_path = os.path.join(docs_dir, "documentation.md")
        with open(docs_path, "w") as f:
            f.write(docs_content)
            
        # Upload to Cloud Storage
        docs_url = await self.storage_service.store_text(
            job_id,
            "docs/documentation.md",
            docs_content
        )
        
        return docs_url


# Singleton instance
_job_service = None

def get_job_service():
    """Dependency to get the job service instance"""
    global _job_service
    if _job_service is None:
        storage_service = get_storage_service()
        _job_service = JobService(storage_service)
    return _job_service