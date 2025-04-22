from fastapi import APIRouter, HTTPException, Depends
from ..models.api import StatusResponse, JobStatus
from ..services.job_service import JobService, get_job_service
import logging

router = APIRouter(prefix="/api")
logger = logging.getLogger(__name__)

@router.get("/status/{job_id}", response_model=StatusResponse)
async def get_job_status(
    job_id: str,
    job_service: JobService = Depends(get_job_service)
):
    """
    Get the current status of a processing job.
    """
    try:
        # Get job from database
        job = await job_service.get_job(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found")
            
        # Build response
        response = {
            "job_id": job["job_id"],
            "status": job["status"],
            "created_at": job["created_at"],
            "updated_at": job["updated_at"],
            "message": job.get("message"),
            "error": job.get("error"),
            "progress": job.get("progress"),
            "current_step": job.get("current_step")
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving job status: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve job status: {str(e)}")