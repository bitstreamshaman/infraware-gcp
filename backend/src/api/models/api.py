from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


class CloudProvider(str, Enum):
    """Supported cloud providers"""
    GCP = "gcp"
    AWS = "aws"
    AZURE = "azure"


class ProcessRequest(BaseModel):
    """Request model for processing a natural language prompt"""
    prompt: str = Field(..., min_length=10, description="Natural language description of desired infrastructure")
    cloud_provider: CloudProvider = Field(default=CloudProvider.GCP, description="Target cloud provider")
    project_name: str = Field(..., min_length=3, description="Name of the project")


class JobStatus(str, Enum):
    """Job processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    DIAGRAMS_READY = "diagrams_ready"
    CONFIRMED = "confirmed"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class JobResponse(BaseModel):
    """Response model with job ID and status"""
    job_id: str = Field(..., description="Unique ID for the job")
    status: JobStatus = Field(..., description="Current status of the job")
    created_at: datetime = Field(..., description="Job creation timestamp")
    updated_at: datetime = Field(..., description="Last job update timestamp")
    message: Optional[str] = Field(None, description="Additional status message")
    error: Optional[str] = Field(None, description="Error message if job failed")


class StatusResponse(JobResponse):
    """Response model for job status"""
    progress: Optional[float] = Field(None, description="Processing progress (0-100)")
    current_step: Optional[str] = Field(None, description="Current processing step")


class DiagramResponse(BaseModel):
    """Response model for diagram generation"""
    job_id: str = Field(..., description="Job ID")
    diagrams: List[Dict[str, str]] = Field(..., description="List of generated diagrams with URLs")


class ConfirmRequest(BaseModel):
    """Request model for confirming diagrams and proceeding with generation"""
    confirmed: bool = Field(..., description="Confirmation flag")
    feedback: Optional[str] = Field(None, description="Optional feedback or adjustments")


class GenerationResponse(BaseModel):
    """Response model for final generation output"""
    job_id: str = Field(..., description="Job ID")
    terraform_files: List[Dict[str, str]] = Field(..., description="List of generated Terraform files with URLs")
    documentation_url: str = Field(..., description="URL to documentation file")
    diagrams: List[Dict[str, str]] = Field(..., description="List of final diagrams with URLs")


class HealthResponse(BaseModel):
    """Response model for health check endpoints"""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    timestamp: str = Field(..., description="Current timestamp")


class ErrorResponse(BaseModel):
    """Response model for errors"""
    error: str = Field(..., description="Error message")