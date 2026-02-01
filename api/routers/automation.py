"""
Automation Router.
Handles automation workflows for batch calling results and conversation callbacks.
Integrates with Zapier, Make, n8n, and custom webhooks.
"""

import logging
import httpx
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from client import get_elevenlabs_client

logger = logging.getLogger("elevenlabs.automation")

router = APIRouter(
    prefix="/automation",
    tags=["Automation"]
)

# In-memory storage for webhook subscriptions (use Redis/DB in production)
webhook_subscriptions: Dict[str, Dict[str, Any]] = {}


class WebhookSubscription(BaseModel):
    """Webhook subscription for receiving batch call results."""
    webhook_url: str = Field(..., description="URL to receive POST callbacks")
    events: List[str] = Field(
        default=["batch.completed", "conversation.completed"],
        description="Events to subscribe to: batch.completed, conversation.completed, call.failed"
    )
    headers: Optional[Dict[str, str]] = Field(None, description="Custom headers to include in webhook calls")
    
    class Config:
        json_schema_extra = {
            "example": {
                "webhook_url": "https://hooks.zapier.com/hooks/catch/xxx/yyy",
                "events": ["batch.completed", "conversation.completed"],
                "headers": {"Authorization": "Bearer your_token"}
            }
        }


class ProcessBatchRequest(BaseModel):
    """Request to process a batch job and send results to webhook."""
    job_id: str = Field(..., description="Batch job ID to process")
    webhook_url: str = Field(..., description="URL to send results to")
    include_transcript: bool = Field(True, description="Include conversation transcripts")
    headers: Optional[Dict[str, str]] = Field(None, description="Custom headers for webhook")
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "btcal_xxx",
                "webhook_url": "https://hooks.zapier.com/hooks/catch/xxx",
                "include_transcript": True
            }
        }


class AutomationResponse(BaseModel):
    """Response for automation endpoints."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


@router.post(
    "/webhooks/subscribe",
    response_model=AutomationResponse,
    summary="Subscribe to Webhook Events",
    description="Register a webhook URL to receive batch call result notifications"
)
async def subscribe_webhook(subscription: WebhookSubscription):
    """
    Subscribe to receive webhook notifications for batch call events.
    
    Events:
    - batch.completed: When all calls in a batch job finish
    - conversation.completed: When each individual call ends
    - call.failed: When a call fails
    
    Your webhook will receive POST requests with the event data.
    """
    import uuid
    subscription_id = f"sub_{uuid.uuid4().hex[:16]}"
    
    webhook_subscriptions[subscription_id] = {
        "id": subscription_id,
        "webhook_url": subscription.webhook_url,
        "events": subscription.events,
        "headers": subscription.headers or {},
        "active": True
    }
    
    logger.info(f"Webhook subscription created: {subscription_id}")
    
    return AutomationResponse(
        success=True,
        message="Webhook subscription created",
        data={"subscription_id": subscription_id}
    )


@router.get(
    "/webhooks/subscriptions",
    summary="List Webhook Subscriptions",
    description="List all active webhook subscriptions"
)
async def list_subscriptions():
    """List all webhook subscriptions."""
    return {
        "subscriptions": list(webhook_subscriptions.values())
    }


@router.delete(
    "/webhooks/subscriptions/{subscription_id}",
    response_model=AutomationResponse,
    summary="Delete Webhook Subscription"
)
async def delete_subscription(subscription_id: str):
    """Delete a webhook subscription."""
    if subscription_id not in webhook_subscriptions:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    del webhook_subscriptions[subscription_id]
    return AutomationResponse(success=True, message="Subscription deleted")


@router.post(
    "/process-batch",
    response_model=AutomationResponse,
    summary="Process Batch Results & Send to Webhook",
    description="Fetch batch job results and send them to your webhook URL"
)
async def process_batch_results(
    request: ProcessBatchRequest,
    background_tasks: BackgroundTasks
):
    """
    Process a completed batch job and send results to your webhook.
    
    This is the main automation endpoint. Call it after your batch job completes
    to get structured results sent to your Zapier/Make/n8n webhook.
    
    The webhook will receive:
    - job_id, job_name, status
    - Total completed/failed counts
    - For each recipient:
      - phone_number
      - status (completed, failed, voicemail)
      - conversation_id
      - transcript (if requested)
      - dynamic_variables used
    """
    # Add to background tasks to respond quickly
    background_tasks.add_task(
        _send_batch_results_to_webhook,
        request.job_id,
        request.webhook_url,
        request.include_transcript,
        request.headers
    )
    
    return AutomationResponse(
        success=True,
        message=f"Processing batch job {request.job_id}. Results will be sent to webhook.",
        data={"job_id": request.job_id, "webhook_url": request.webhook_url}
    )


async def _send_batch_results_to_webhook(
    job_id: str,
    webhook_url: str,
    include_transcript: bool,
    headers: Optional[Dict[str, str]]
):
    """Background task to fetch and send batch results."""
    try:
        client = get_elevenlabs_client()
        
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
                "outcome": None
            }
            
            # Fetch conversation if requested
            if include_transcript and recipient.get("conversation_id") and recipient.get("status") == "completed":
                try:
                    conv = client.conversations.get_conversation(recipient["conversation_id"])
                    
                    # Build transcript
                    transcript_text = []
                    for turn in conv.get("transcript", []):
                        role = turn.get("role", "unknown")
                        message = turn.get("message") or turn.get("original_message", "")
                        transcript_text.append(f"{role}: {message}")
                    
                    result["transcript"] = "\n".join(transcript_text)
                    result["duration_seconds"] = conv.get("metadata", {}).get("call_duration_secs")
                    
                except Exception as e:
                    logger.warning(f"Could not fetch conversation: {e}")
            
            results.append(result)
        
        # Build payload
        payload = {
            "event": "batch.completed",
            "job_id": job_id,
            "job_name": job.get("name"),
            "status": job.get("status"),
            "total_recipients": len(recipients),
            "completed": sum(1 for r in results if r["status"] == "completed"),
            "failed": sum(1 for r in results if r["status"] != "completed"),
            "results": results
        }
        
        # Send to webhook
        async with httpx.AsyncClient(timeout=30.0) as http_client:
            webhook_headers = {"Content-Type": "application/json"}
            if headers:
                webhook_headers.update(headers)
            
            response = await http_client.post(
                webhook_url,
                json=payload,
                headers=webhook_headers
            )
            
            logger.info(f"Webhook sent to {webhook_url}: status={response.status_code}")
            
    except Exception as e:
        logger.error(f"Error sending batch results to webhook: {e}")


@router.post(
    "/analyze-conversation",
    summary="Analyze Conversation Outcome",
    description="Use AI to analyze a conversation transcript and determine outcome"
)
async def analyze_conversation(
    conversation_id: str,
    outcomes: List[str] = ["interested", "not_interested", "callback_requested", "voicemail", "no_answer"]
):
    """
    Analyze a conversation to determine the outcome.
    
    Returns a classification of the conversation based on the transcript.
    Useful for triggering different automation paths.
    
    Example outcomes:
    - interested: Customer showed interest
    - not_interested: Customer declined
    - callback_requested: Customer asked to call back later
    - voicemail: Left voicemail
    - no_answer: No answer/busy
    """
    try:
        client = get_elevenlabs_client()
        conv = client.conversations.get_conversation(conversation_id)
        
        transcript = conv.get("transcript", [])
        status = conv.get("status")
        metadata = conv.get("metadata", {})
        
        # Simple rule-based analysis (you can enhance with AI)
        outcome = "unknown"
        confidence = 0.5
        
        # Build transcript text for analysis
        transcript_text = " ".join([
            (t.get("message") or t.get("original_message", "")).lower()
            for t in transcript
        ])
        
        # Basic keyword matching (enhance with LLM for better accuracy)
        if not transcript or len(transcript) < 2:
            if metadata.get("termination_reason") == "voicemail":
                outcome = "voicemail"
                confidence = 0.9
            else:
                outcome = "no_answer"
                confidence = 0.8
        elif any(word in transcript_text for word in ["yes", "interested", "tell me more", "sounds good", "i want"]):
            outcome = "interested"
            confidence = 0.7
        elif any(word in transcript_text for word in ["no", "not interested", "don't call", "stop"]):
            outcome = "not_interested"
            confidence = 0.7
        elif any(word in transcript_text for word in ["call back", "later", "busy", "another time"]):
            outcome = "callback_requested"
            confidence = 0.7
        else:
            outcome = "completed"
            confidence = 0.5
        
        return {
            "conversation_id": conversation_id,
            "outcome": outcome,
            "confidence": confidence,
            "duration_seconds": metadata.get("call_duration_secs"),
            "transcript_turns": len(transcript),
            "suggested_action": _get_suggested_action(outcome)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _get_suggested_action(outcome: str) -> str:
    """Get suggested automation action based on outcome."""
    actions = {
        "interested": "send_followup_email, schedule_meeting",
        "not_interested": "update_crm_status, add_to_dnc_list",
        "callback_requested": "schedule_callback, send_reminder",
        "voicemail": "send_sms, schedule_retry",
        "no_answer": "schedule_retry, send_sms",
        "completed": "update_crm_status",
        "unknown": "manual_review"
    }
    return actions.get(outcome, "manual_review")
