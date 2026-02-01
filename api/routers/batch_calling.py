"""
Batch Calling Router.
Handles batch calling job submission and management endpoints.
"""

import logging
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

logger = logging.getLogger("elevenlabs.batch_calling.router")

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
    
    Features:
    - Include ecommerce_credentials to enable product/order lookups during all calls
    - Include recipient email addresses to enable email templates during calls
    - Include sender_email for the business/sender email header
    
    Example use cases:
    - Marketing campaigns with product info
    - Appointment reminders with confirmation emails
    - Customer surveys
    - Payment reminders
    """
    try:
        # Convert recipients to dict format with conversation_initiation_client_data
        recipients = []
        for r in request.recipients:
            recipient_data = {
                "phone_number": r.phone_number
            }
            if r.name:
                recipient_data["name"] = r.name
            # Dynamic variables must be inside conversation_initiation_client_data
            if r.dynamic_variables:
                recipient_data["conversation_initiation_client_data"] = {
                    "dynamic_variables": r.dynamic_variables
                }
            recipients.append(recipient_data)
        
        # Debug: log the request
        logger.info(f"Batch calling request: agent_id={request.agent_id}, phone_number_id={request.phone_number_id}, recipients={len(recipients)}")
        
        result = client.batch_calling.submit_job(
            call_name=request.call_name,
            agent_id=request.agent_id,
            recipients=recipients,
            phone_number_id=request.phone_number_id,
            scheduled_time_unix=request.scheduled_time_unix,
            timezone=request.timezone,
            retry_count=request.retry_count
        )
        
        job_id = result.get("id")
        
        # Store batch job context for webhooks
        if request.ecommerce_credentials or request.sender_email or any(r.email for r in request.recipients):
            from ecommerce import get_batch_job_context
            batch_context = get_batch_job_context()
            
            # Prepare ecommerce credentials dict
            ecom_creds = None
            if request.ecommerce_credentials:
                ecom_creds = request.ecommerce_credentials.model_dump()
            
            # Prepare recipient list with email info
            recipients_with_email = [
                {
                    "phone_number": r.phone_number,
                    "name": r.name,
                    "email": r.email
                }
                for r in request.recipients
            ]
            
            batch_context.store_job(
                job_id=job_id,
                agent_id=request.agent_id,
                ecommerce_credentials=ecom_creds,
                sender_email=request.sender_email,
                recipients=recipients_with_email
            )
            
            logger.info(
                f"Batch job {job_id} context stored: "
                f"ecommerce={'enabled' if ecom_creds else 'disabled'}, "
                f"sender_email={request.sender_email or 'none'}, "
                f"recipients_with_email={sum(1 for r in request.recipients if r.email)}"
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


@router.get(
    "/{job_id}/results",
    summary="Get Batch Job Results with Transcripts",
    description="Get detailed results including conversation transcripts for automation"
)
async def get_batch_job_results(
    job_id: str,
    include_transcript: bool = Query(True, description="Include conversation transcripts"),
    client: ElevenLabsClient = Depends(get_client)
):
    """
    Get batch job results with conversation details for automation.
    
    Returns structured data for each recipient including:
    - Call status (completed, failed, voicemail, etc.)
    - Conversation transcript
    - Dynamic variables used
    - Duration
    
    Use this endpoint to:
    1. Process completed calls
    2. Trigger follow-up actions based on outcomes
    3. Update your CRM/database with results
    """
    try:
        # Get batch job details
        job = client.batch_calling.get_job(job_id)
        recipients = job.get("recipients", [])
        
        results = []
        for recipient in recipients:
            result = {
                "recipient_id": recipient.get("id"),
                "phone_number": recipient.get("phone_number"),
                "status": recipient.get("status"),
                "conversation_id": recipient.get("conversation_id"),
                "dynamic_variables": recipient.get("conversation_initiation_client_data", {}).get("dynamic_variables", {}),
                "transcript": None,
                "duration_seconds": None,
                "call_successful": recipient.get("status") == "completed"
            }
            
            # Fetch conversation details if requested and conversation exists
            if include_transcript and recipient.get("conversation_id"):
                try:
                    conv = client.conversations.get_conversation(recipient["conversation_id"])
                    
                    # Extract transcript
                    transcript_messages = []
                    for turn in conv.get("transcript", []):
                        transcript_messages.append({
                            "role": turn.get("role"),
                            "message": turn.get("message") or turn.get("original_message", "")
                        })
                    
                    result["transcript"] = transcript_messages
                    result["duration_seconds"] = conv.get("metadata", {}).get("call_duration_secs")
                    result["end_reason"] = conv.get("metadata", {}).get("termination_reason")
                    
                except Exception as e:
                    logger.warning(f"Could not fetch conversation {recipient.get('conversation_id')}: {e}")
            
            results.append(result)
        
        return {
            "job_id": job_id,
            "job_name": job.get("name"),
            "status": job.get("status"),
            "total_recipients": len(recipients),
            "completed": sum(1 for r in results if r["call_successful"]),
            "failed": sum(1 for r in results if not r["call_successful"]),
            "results": results
        }
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ElevenLabsError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))
