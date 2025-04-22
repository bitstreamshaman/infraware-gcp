from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from ..models.api import ConfirmRequest, JobResponse, JobStatus
from ..services.job_service import JobService, get_job_service
import logging
from datetime import datetime

router = APIRouter(prefix="/api")
logger = logging.getLogger(__name__)

@router.post("/confirm/{job_id}", response_model=JobResponse)
async def confirm_diagrams(
    job_id: str,
    request: ConfirmRequest,
    background_tasks: BackgroundTasks,
    job_service: JobService = Depends(get_job_service)
):
    """
    Confirm the diagrams and proceed with Terraform generation.
    This endpoint should be called after reviewing the diagrams.
    """
    try:
        # Get job from database
        job = await job_service.get_job(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found")
            
        # Check job status
        if job["status"] != JobStatus.DIAGRAMS_READY:
            raise HTTPException(
                status_code=400, 
                detail=f"Job is not in the diagrams_ready state. Current status: {job['status']}"
            )
            
        # Only proceed if user confirmed
        if not request.confirmed:
            await job_service.update_job(job_id, {
                "status": JobStatus.FAILED,
                "updated_at": datetime.utcnow(),
                "error": "User rejected the diagrams",
                "message": request.feedback if request.feedback else "Diagrams rejected by user"
            })
            
            return {
                "job_id": job_id,
                "status": JobStatus.FAILED,
                "created_at": job["created_at"],
                "updated_at": datetime.utcnow(),
                "message": "Generation cancelled by user",
                "error": "User rejected the diagrams"
            }
            
        # after confirming
        await job_service.update_job(job_id, {
            "yaml_content": job["yaml_url"],  # or fetch from GCS if needed
        })

        
        # Start background processing for Terraform generation
        background_tasks.add_task(
            job_service.generate_terraform,
            job_id=job_id
        )
        
        return {
            "job_id": job_id,
            "status": JobStatus.CONFIRMED,
            "created_at": job["created_at"],
            "updated_at": datetime.utcnow(),
            "message": "User confirmed diagrams, generating Terraform..."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing confirmation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process confirmation: {str(e)}")