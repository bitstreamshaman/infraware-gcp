from typing import Dict, Any, Optional
from ..models.api import JobStatus
from datetime import datetime
import logging
import asyncio

logger = logging.getLogger(__name__)

class JobService:
    """Service for managing job processing and status"""
    
    def __init__(self):
        """Initialize the job service with an in-memory job store for now"""
        self.jobs = {}  # In-memory job storage for development
    
    async def create_job(self, job_data: Dict[str, Any]) -> str:
        """Create a new job and store it"""
        job_id = job_data["job_id"]
        self.jobs[job_id] = job_data
        return job_id
    
    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job data by ID"""
        return self.jobs.get(job_id)
    
    async def update_job(self, job_id: str, updates: Dict[str, Any]) -> bool:
        """Update job data"""
        if job_id not in self.jobs:
            return False
        
        self.jobs[job_id].update(updates)
        return True
    
    async def process_job(self, job_id: str, prompt: str, cloud_provider: str, project_name: str):
        """
        Process a job asynchronously.
        This is a placeholder for the actual CrewAI integration.
        """
        try:
            # Update job status to processing
            await self.update_job(job_id, {
                "status": JobStatus.PROCESSING,
                "updated_at": datetime.utcnow(),
                "current_step": "Generating YAML from natural language",
                "progress": 10
            })
            
            # Simulate YAML generation (will be replaced with CrewAI)
            await asyncio.sleep(2)  # Simulating work
            
            # Update progress
            await self.update_job(job_id, {
                "updated_at": datetime.utcnow(),
                "current_step": "Validating YAML",
                "progress": 30
            })
            
            # Simulate validation
            await asyncio.sleep(1)  # Simulating work
            
            # Update progress
            await self.update_job(job_id, {
                "updated_at": datetime.utcnow(),
                "current_step": "Generating diagrams",
                "progress": 50
            })
            
            # Simulate diagram generation
            await asyncio.sleep(2)  # Simulating work
            
            # Mark diagrams as ready
            await self.update_job(job_id, {
                "status": JobStatus.DIAGRAMS_READY,
                "updated_at": datetime.utcnow(),
                "current_step": "Waiting for user confirmation",
                "progress": 70,
                "message": "Diagrams are ready for review"
            })
            
        except Exception as e:
            logger.error(f"Error processing job {job_id}: {str(e)}", exc_info=True)
            await self.update_job(job_id, {
                "status": JobStatus.FAILED,
                "updated_at": datetime.utcnow(),
                "error": f"Processing failed: {str(e)}",
                "message": "Job processing failed"
            })
    
    async def generate_terraform(self, job_id: str):
        """
        Generate Terraform files after user confirmation.
        This is a placeholder for the actual CrewAI integration.
        """
        try:
            # Update job status to generating
            await self.update_job(job_id, {
                "status": JobStatus.GENERATING,
                "updated_at": datetime.utcnow(),
                "current_step": "Converting YAML to Terraform",
                "progress": 80
            })
            
            # Simulate Terraform generation (will be replaced with CrewAI)
            await asyncio.sleep(3)  # Simulating work
            
            # Update progress
            await self.update_job(job_id, {
                "updated_at": datetime.utcnow(),
                "current_step": "Generating documentation",
                "progress": 90
            })
            
            # Simulate documentation generation
            await asyncio.sleep(2)  # Simulating work
            
            # Mark job as completed
            await self.update_job(job_id, {
                "status": JobStatus.COMPLETED,
                "updated_at": datetime.utcnow(),
                "current_step": "Completed",
                "progress": 100,
                "message": "Infrastructure as Code generation complete"
            })
            
        except Exception as e:
            logger.error(f"Error generating Terraform for job {job_id}: {str(e)}", exc_info=True)
            await self.update_job(job_id, {
                "status": JobStatus.FAILED,
                "updated_at": datetime.utcnow(),
                "error": f"Terraform generation failed: {str(e)}",
                "message": "Terraform generation failed"
            })

# Singleton instance
_job_service = None

def get_job_service():
    """Dependency to get the job service instance"""
    global _job_service
    if _job_service is None:
        _job_service = JobService()
    return _job_service