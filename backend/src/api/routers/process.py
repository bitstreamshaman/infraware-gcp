from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from ..models.api import ProcessRequest, JobResponse, JobStatus
from ..services.job_service import JobService, get_job_service
from ..services.storage_service import StorageService, get_storage_service
import uuid
from datetime import datetime
import logging

router = APIRouter(prefix="/api")
logger = logging.getLogger(__name__)

@router.post("/process", response_model=JobResponse, status_code=202)
async def process_nl_prompt(
    request: ProcessRequest,
    background_tasks: BackgroundTasks,
    job_service: JobService = Depends(get_job_service),
    storage_service: StorageService = Depends(get_storage_service)
):
    """
    Process a natural language prompt and start the IaC generation workflow.
    This is an asynchronous endpoint that returns a job ID for tracking.
    """
    try:
        # Create a new job
        job_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        # Initialize job in database
        job_data = {
            "job_id": job_id,
            "status": JobStatus.PENDING,
            "created_at": now,
            "updated_at": now,
            "prompt": request.prompt,
            "cloud_provider": request.cloud_provider,
            "project_name": request.project_name
        }
        
        # Save the job
        await job_service.create_job(job_data)
        
        # Start background processing
        background_tasks.add_task(
            job_service.process_job,
            job_id=job_id,
            prompt=request.prompt,
            cloud_provider=request.cloud_provider,
            project_name=request.project_name
        )
        
        return {
            "job_id": job_id,
            "status": JobStatus.PENDING,
            "created_at": now,
            "updated_at": now,
            "message": "Job created and processing started"
        }
        
    except Exception as e:
        logger.error(f"Error starting processing job: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start processing: {str(e)}")