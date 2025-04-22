from fastapi import APIRouter, HTTPException, Depends
from ..models.api import DiagramResponse, JobStatus
from ..services.job_service import JobService, get_job_service
from ..services.storage_service import StorageService, get_storage_service
import logging

router = APIRouter(prefix="/api")
logger = logging.getLogger(__name__)

@router.get("/diagrams/{job_id}", response_model=DiagramResponse)
async def get_diagrams(
    job_id: str,
    job_service: JobService = Depends(get_job_service),
    storage_service: StorageService = Depends(get_storage_service)
):
    """
    Get the generated architecture diagrams for a job.
    This endpoint should be called after job status is 'diagrams_ready'.
    """
    try:
        # Get job from database
        job = await job_service.get_job(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found")
            
        # Check job status
        if job["status"] not in [JobStatus.DIAGRAMS_READY, JobStatus.CONFIRMED, JobStatus.GENERATING, JobStatus.COMPLETED]:
            raise HTTPException(
                status_code=400, 
                detail=f"Diagrams not yet available. Current status: {job['status']}"
            )
            
        # Get diagram URLs from storage
        try:
            diagrams = await storage_service.get_diagram_urls(job_id)
            
            if not diagrams:
                raise HTTPException(status_code=404, detail=f"No diagrams found for job {job_id}")
                
            return {
                "job_id": job_id,
                "diagrams": diagrams
            }
            
        except Exception as e:
            logger.error(f"Error retrieving diagrams: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to retrieve diagrams: {str(e)}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing diagram request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process diagram request: {str(e)}")