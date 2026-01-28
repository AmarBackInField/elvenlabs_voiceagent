"""
Batch Calling Router.
Handles batch calling job submission and management endpoints.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from client import ElevenLabsClient
from api.dependencies import get_client
from api.schemas import (
    SubmitBatchJobRequest,
    BatchJobResponse,
    BatchJobListResponse,
    BatchJobCallsResponse,
    SuccessResponse,
    ErrorResponse
)
from exceptions import ElevenLabsError, NotFoundError


router = APIRouter(
    prefix="/batch-calling",
    tags=["Batch Calling"],
    responses={
        401: {"model": ErrorResponse, "description": "Authentication failed"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)


@router.post(
    "/submit",
    response_model=BatchJobResponse,
    status_code=201,
    summary="Submit Batch Calling Job",
    description="Submit a batch call request to schedule calls for multiple recipients"
)
async def submit_batch_job(
    request: SubmitBatchJobRequest,
    client: ElevenLabsClient = Depends(get_client)
):
    """
    Submit a batch calling job to call multiple recipients.
    
    The agent will sequentially or concurrently call each recipient.
    You can include dynamic variables for personalization per recipient.
    
    Example use cases:
    - Marketing campaigns
    - Appointment reminders
    - Customer surveys
    - Payment reminders
    """
    try:
        # Convert recipients to dict format
        recipients = [
            r.model_dump(exclude_none=True) 
            for r in request.recipients
        ]
        
        result = client.batch_calling.submit_job(
            call_name=request.call_name,
            agent_id=request.agent_id,
            recipients=recipients,
            phone_number_id=request.phone_number_id,
            scheduled_time_unix=request.scheduled_time_unix,
            timezone=request.timezone,
            retry_count=request.retry_count
        )
        
        return BatchJobResponse(**result)
        
    except ElevenLabsError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@router.get(
    "",
    response_model=BatchJobListResponse,
    summary="List Batch Jobs",
    description="Get a list of all batch calling jobs"
)
async def list_batch_jobs(
    status: Optional[str] = Query(
        None, 
        description="Filter by status (pending, running, completed, failed)"
    ),
    cursor: Optional[str] = Query(None, description="Pagination cursor"),
    page_size: int = Query(30, ge=1, le=100, description="Results per page"),
    client: ElevenLabsClient = Depends(get_client)
):
    """
    List all batch calling jobs with optional filtering.
    
    Filter by status:
    - pending: Jobs waiting to start
    - running: Jobs currently in progress
    - completed: Successfully finished jobs
    - failed: Jobs that encountered errors
    """
    try:
        result = client.batch_calling.list_jobs(
            status=status,
            cursor=cursor,
            page_size=page_size
        )
        return BatchJobListResponse(
            jobs=result.get("jobs", []),
            cursor=result.get("cursor")
        )
    except ElevenLabsError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@router.get(
    "/{job_id}",
    response_model=BatchJobResponse,
    summary="Get Batch Job",
    description="Get details and status of a specific batch job",
    responses={404: {"model": ErrorResponse, "description": "Job not found"}}
)
async def get_batch_job(
    job_id: str,
    client: ElevenLabsClient = Depends(get_client)
):
    """
    Get details of a batch calling job.
    
    Returns current status, progress, and statistics.
    """
    try:
        result = client.batch_calling.get_job(job_id)
        return BatchJobResponse(**result)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ElevenLabsError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@router.get(
    "/{job_id}/calls",
    response_model=BatchJobCallsResponse,
    summary="Get Batch Job Calls",
    description="Get individual call results from a batch job",
    responses={404: {"model": ErrorResponse, "description": "Job not found"}}
)
async def get_batch_job_calls(
    job_id: str,
    status: Optional[str] = Query(None, description="Filter calls by status"),
    cursor: Optional[str] = Query(None, description="Pagination cursor"),
    page_size: int = Query(50, ge=1, le=100, description="Results per page"),
    client: ElevenLabsClient = Depends(get_client)
):
    """
    Get individual call results from a batch job.
    
    Shows the status of each call in the batch.
    """
    try:
        result = client.batch_calling.get_job_calls(
            job_id=job_id,
            status=status,
            cursor=cursor,
            page_size=page_size
        )
        return BatchJobCallsResponse(
            calls=result.get("calls", []),
            cursor=result.get("cursor")
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ElevenLabsError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@router.post(
    "/{job_id}/cancel",
    response_model=SuccessResponse,
    summary="Cancel Batch Job",
    description="Cancel a running or pending batch job",
    responses={404: {"model": ErrorResponse, "description": "Job not found"}}
)
async def cancel_batch_job(
    job_id: str,
    client: ElevenLabsClient = Depends(get_client)
):
    """
    Cancel a batch calling job.
    
    Stops any pending calls. Calls already in progress will complete.
    """
    try:
        client.batch_calling.cancel_job(job_id)
        return SuccessResponse(message=f"Batch job {job_id} cancelled successfully")
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ElevenLabsError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))
