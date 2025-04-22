from fastapi import APIRouter, HTTPException, Depends
from ..models.api import GenerationResponse, JobStatus
from ..services.job_service import JobService, get_job_service
from ..services.storage_service import StorageService, get_storage_service
import logging

router = APIRouter(prefix="/api")
logger = logging.getLogger(__name__)

@router.get("/generate/{job_id}", response_model=GenerationResponse)
async def get_generated_output(
    job_id: str,
    job_service: JobService = Depends(get_job_service),
    storage_service: StorageService = Depends(get_storage_service)
):
    """
    Get the generated Terraform files, documentation, and diagrams.
    This endpoint should be called after job status is 'completed'.
    """
    try:
        # Get job from database
        job = await job_service.get_job(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found")
            
        # Check job status
        if job["status"] != JobStatus.COMPLETED:
            raise HTTPException(
                status_code=400, 
                detail=f"Generation not yet complete. Current status: {job['status']}"
            )
            
        # Get generated files from storage
        try:
            terraform_files = await storage_service.get_terraform_urls(job_id)
            documentation_url = await storage_service.get_documentation_url(job_id)
            diagrams = await storage_service.get_diagram_urls(job_id)
            
            if not terraform_files:
                raise HTTPException(status_code=404, detail=f"No Terraform files found for job {job_id}")
                
            if not documentation_url:
                raise HTTPException(status_code=404, detail=f"No documentation found for job {job_id}")
                
            return {
                "job_id": job_id,
                "terraform_files": terraform_files,
                "documentation_url": documentation_url,
                "diagrams": diagrams
            }
            
        except Exception as e:
            logger.error(f"Error retrieving generated files: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to retrieve generated files: {str(e)}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing generation request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process generation request: {str(e)}")