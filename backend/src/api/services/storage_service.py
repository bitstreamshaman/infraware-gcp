from typing import List, Dict, Optional
import logging
import os
from datetime import datetime, timedelta
import tempfile
from ..config import settings
import os

logger = logging.getLogger(__name__)

class StorageService:
    """Service for managing file storage in GCP Cloud Storage"""
    
    def __init__(self):
        """Initialize the storage service"""
        self.bucket_name = settings.GCP_STORAGE_BUCKET or "nl-to-iac-artifacts"
        
        # Force local mode for development
        self.local_mode = True  # Always use local mode for development
        logger.warning("Running in local storage mode - files will be stored locally")
        self.local_dir = os.path.join(tempfile.gettempdir(), "nl-to-iac")
        os.makedirs(self.local_dir, exist_ok=True)
        
        # Only initialize GCP client if not in local mode (this won't run in our case)
        if not self.local_mode:
            from google.cloud import storage
            self.client = storage.Client()
            try:
                self.bucket = self.client.get_bucket(self.bucket_name)
            except Exception as e:
                logger.info(f"Bucket {self.bucket_name} not found, creating...")
                self.bucket = self.client.create_bucket(self.bucket_name)
    
    async def get_diagram_urls(self, job_id: str) -> List[Dict[str, str]]:
        """Get URLs for all diagrams associated with a job."""
        # In local mode, use local paths
        diagrams_dir = os.path.join(self.local_dir, job_id, "diagrams")
        if not os.path.exists(diagrams_dir):
            os.makedirs(diagrams_dir, exist_ok=True)
            
        # Create a placeholder diagram if none exists
        placeholder_path = os.path.join(diagrams_dir, "architecture.svg")
        if not os.path.exists(placeholder_path):
            with open(placeholder_path, "w") as f:
                f.write(f'''<svg width="400" height="200" xmlns="http://www.w3.org/2000/svg">
                    <rect width="100%" height="100%" fill="#f0f0f0" />
                    <text x="50%" y="50%" text-anchor="middle" font-family="Arial" font-size="16">
                        {job_id} Architecture Diagram
                    </text>
                </svg>''')
        
        # List all files in the diagrams directory
        diagram_files = []
        for filename in os.listdir(diagrams_dir):
            file_path = os.path.join(diagrams_dir, filename)
            if os.path.isfile(file_path):
                diagram_files.append(filename)
        
        # If no diagrams found, create a default one
        if not diagram_files:
            filename = "architecture.svg"
            file_path = os.path.join(diagrams_dir, filename)
            with open(file_path, "w") as f:
                f.write(f'''<svg width="400" height="200" xmlns="http://www.w3.org/2000/svg">
                    <rect width="100%" height="100%" fill="#f0f0f0" />
                    <text x="50%" y="50%" text-anchor="middle" font-family="Arial" font-size="16">
                        {job_id} Architecture Diagram
                    </text>
                </svg>''')
            diagram_files.append(filename)
        
        # Return URLs for all diagrams
        return [
            {
                "name": filename,
                "url": f"/api/static/{job_id}/diagrams/{filename}",
                "type": self._get_content_type(filename)
            }
            for filename in diagram_files
        ]
    
    async def get_terraform_urls(self, job_id: str) -> List[Dict[str, str]]:
        """Get URLs for all Terraform files associated with a job."""
        # In local mode, use local paths and create placeholder files
        terraform_dir = os.path.join(self.local_dir, job_id, "terraform")
        if not os.path.exists(terraform_dir):
            os.makedirs(terraform_dir, exist_ok=True)
            
        # Create placeholder Terraform files if they don't exist
        placeholders = {
            "main.tf": f'# Terraform configuration for {job_id}\n\nresource "random_id" "id" {{\n  byte_length = 8\n}}',
            "variables.tf": 'variable "project_name" {\n  type = string\n  description = "Name of the project"\n}',
            "outputs.tf": 'output "project_id" {\n  value = random_id.id.hex\n  description = "The project ID"\n}'
        }
        
        for filename, content in placeholders.items():
            file_path = os.path.join(terraform_dir, filename)
            if not os.path.exists(file_path):
                with open(file_path, "w") as f:
                    f.write(content)
        
        # List all files in the terraform directory
        terraform_files = []
        for filename in os.listdir(terraform_dir):
            file_path = os.path.join(terraform_dir, filename)
            if os.path.isfile(file_path):
                terraform_files.append(filename)
        
        # Return URLs for all Terraform files
        return [
            {
                "name": filename,
                "url": f"/api/static/{job_id}/terraform/{filename}",
                "type": "text/plain"
            }
            for filename in terraform_files
        ]
    
    async def get_documentation_url(self, job_id: str) -> str:
        """Get URL for the documentation file associated with a job."""
        # In local mode, use local path and create placeholder file
        docs_dir = os.path.join(self.local_dir, job_id, "docs")
        if not os.path.exists(docs_dir):
            os.makedirs(docs_dir, exist_ok=True)
            
        # Create placeholder documentation file if it doesn't exist
        docs_path = os.path.join(docs_dir, "documentation.md")
        if not os.path.exists(docs_path):
            with open(docs_path, "w") as f:
                f.write(f"# Project Documentation\n\nThis is a placeholder documentation file for job {job_id}.\n\n## Architecture\n\nPlease refer to the architecture diagram for an overview of the system design.")
        
        return f"/api/static/{job_id}/docs/documentation.md"
    
    async def store_file(self, job_id: str, file_path: str, file_content: bytes) -> str:
        """
        Store a file in local storage and return its URL.
        
        Args:
            job_id: The ID of the job
            file_path: Relative path within the job's folder
            file_content: File content as bytes
            
        Returns:
            URL to access the file
        """
        # Full local path
        local_path = os.path.join(self.local_dir, job_id, file_path)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        with open(local_path, "wb") as f:
            f.write(file_content)
            
        return f"/api/static/{job_id}/{file_path}"
    
    async def store_text(self, job_id: str, file_path: str, content: str) -> str:
        """Store text content and return its URL."""
        return await self.store_file(job_id, file_path, content.encode('utf-8'))
    
    async def get_signed_url(self, file_path: str, expires_in_minutes: int = 60) -> str:
        """Generate a signed URL for accessing a file."""
        # In local mode, just return a simple path
        return f"/api/static/{file_path}"
    
    def _get_content_type(self, file_name: str) -> str:
        """Get the content type based on file extension."""
        ext = os.path.splitext(file_name)[1].lower()
        
        content_types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.svg': 'image/svg+xml',
            '.md': 'text/markdown',
            '.tf': 'text/plain',
            '.json': 'application/json',
            '.yaml': 'text/yaml',
            '.yml': 'text/yaml',
        }
        
        return content_types.get(ext, 'application/octet-stream')


# Singleton instance
_storage_service = None

def get_storage_service():
    """Dependency to get the storage service instance"""
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service