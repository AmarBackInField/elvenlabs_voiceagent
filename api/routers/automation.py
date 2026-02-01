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


@router.get(
    "/batch/{job_id}/wait-and-get-results",
    summary="Wait for Batch Completion & Get Results",
    description="Automatically polls until batch job completes, then returns full results with transcripts"
)
async def wait_and_get_batch_results(
    job_id: str,
    include_transcript: bool = True,
    extract_appointments: bool = True,
    max_wait_seconds: int = 300,
    poll_interval: int = 5
):
    """
    Automatically wait for a batch job to complete and return full results.
    
    This endpoint:
    1. Polls the batch job status every {poll_interval} seconds
    2. Waits until status == "completed" (or max_wait_seconds reached)
    3. Fetches all conversation transcripts
    4. Optionally extracts appointment data from each conversation
    
    Parameters:
    - job_id: The batch job ID
    - include_transcript: Include full conversation transcripts
    - extract_appointments: Run LLM/rule extraction on each conversation
    - max_wait_seconds: Maximum time to wait (default 5 minutes)
    - poll_interval: Seconds between status checks (default 5)
    
    Returns complete results when batch finishes.
    """
    import asyncio
    
    client = get_elevenlabs_client()
    elapsed = 0
    
    # Poll until completed or timeout
    while elapsed < max_wait_seconds:
        try:
            job = client.batch_calling.get_job(job_id)
            status = job.get("status")
            
            if status == "completed":
                break
            elif status in ["failed", "cancelled"]:
                return {
                    "job_id": job_id,
                    "status": status,
                    "error": f"Batch job {status}",
                    "results": []
                }
            
            # Still in progress, wait and poll again
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
            
        except Exception as e:
            logger.error(f"Error polling batch job: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    if elapsed >= max_wait_seconds:
        return {
            "job_id": job_id,
            "status": "timeout",
            "error": f"Batch job did not complete within {max_wait_seconds} seconds",
            "elapsed_seconds": elapsed,
            "results": []
        }
    
    # Job completed - fetch full results
    try:
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
                "extracted_data": None
            }
            
            conv_id = recipient.get("conversation_id")
            
            # Fetch conversation details
            if conv_id and recipient.get("status") == "completed":
                try:
                    conv = client.conversations.get_conversation(conv_id)
                    
                    # Build transcript
                    if include_transcript:
                        transcript_messages = []
                        for turn in conv.get("transcript", []):
                            transcript_messages.append({
                                "role": turn.get("role"),
                                "message": turn.get("message") or turn.get("original_message", "")
                            })
                        result["transcript"] = transcript_messages
                    
                    result["duration_seconds"] = conv.get("metadata", {}).get("call_duration_secs")
                    
                    # Extract appointment data
                    if extract_appointments:
                        transcript_text = "\n".join([
                            f"{t.get('role', 'unknown').upper()}: {t.get('message') or t.get('original_message', '')}"
                            for t in conv.get("transcript", [])
                        ])
                        extraction = await _extract_appointment_rules(conv_id, transcript_text, conv.get("transcript", []))
                        result["extracted_data"] = extraction.get("extracted_data")
                    
                except Exception as e:
                    logger.warning(f"Could not fetch conversation {conv_id}: {e}")
            
            results.append(result)
        
        return {
            "job_id": job_id,
            "job_name": job.get("name"),
            "status": "completed",
            "total_recipients": len(recipients),
            "completed_calls": sum(1 for r in results if r["status"] == "completed"),
            "failed_calls": sum(1 for r in results if r["status"] != "completed"),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error fetching batch results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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


class AppointmentExtraction(BaseModel):
    """Extracted appointment details from conversation."""
    wants_appointment: bool = Field(..., description="Whether user wants to book an appointment")
    appointment_date: Optional[str] = Field(None, description="Appointment date (YYYY-MM-DD format)")
    appointment_time: Optional[str] = Field(None, description="Appointment time (HH:MM format, 24hr)")
    purpose: Optional[str] = Field(None, description="Purpose/reason for appointment")
    customer_name: Optional[str] = Field(None, description="Customer name if mentioned")
    additional_notes: Optional[str] = Field(None, description="Any other relevant notes")
    confidence: float = Field(0.0, description="Confidence score 0-1")


class ExtractDataRequest(BaseModel):
    """Request for extracting data from conversation."""
    conversation_id: str = Field(..., description="Conversation ID to analyze")
    extraction_type: str = Field("appointment", description="Type of extraction: appointment, lead, support")
    openai_api_key: Optional[str] = Field(None, description="OpenAI API key (uses env var if not provided)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": "conv_xxx",
                "extraction_type": "appointment"
            }
        }


@router.post(
    "/extract-data",
    summary="Extract Structured Data from Conversation",
    description="Use LLM to extract appointment details, lead info, or other structured data from transcript"
)
async def extract_conversation_data(request: ExtractDataRequest):
    """
    Extract structured data from a conversation transcript using LLM.
    
    For appointment extraction, returns:
    - wants_appointment: true/false
    - appointment_date: YYYY-MM-DD
    - appointment_time: HH:MM (24hr)
    - purpose: reason for appointment
    - customer_name: if mentioned
    - additional_notes: other details
    
    Requires OPENAI_API_KEY environment variable or passed in request.
    """
    import os
    import json
    
    try:
        client = get_elevenlabs_client()
        conv = client.conversations.get_conversation(request.conversation_id)
        
        transcript = conv.get("transcript", [])
        
        # Build transcript text
        transcript_text = "\n".join([
            f"{t.get('role', 'unknown').upper()}: {t.get('message') or t.get('original_message', '')}"
            for t in transcript
        ])
        
        if not transcript_text.strip():
            return {
                "conversation_id": request.conversation_id,
                "extraction_type": request.extraction_type,
                "error": "Empty transcript",
                "extracted_data": None
            }
        
        # Get OpenAI API key
        api_key = request.openai_api_key or os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            # Fallback to rule-based extraction
            return await _extract_appointment_rules(request.conversation_id, transcript_text, transcript)
        
        # Use OpenAI for extraction
        extraction_prompt = _get_extraction_prompt(request.extraction_type, transcript_text)
        
        async with httpx.AsyncClient(timeout=30.0) as http_client:
            response = await http_client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": "You are a data extraction assistant. Extract structured data from conversation transcripts. Return valid JSON only."},
                        {"role": "user", "content": extraction_prompt}
                    ],
                    "temperature": 0,
                    "response_format": {"type": "json_object"}
                }
            )
            
            if response.status_code != 200:
                logger.error(f"OpenAI API error: {response.text}")
                # Fallback to rules
                return await _extract_appointment_rules(request.conversation_id, transcript_text, transcript)
            
            result = response.json()
            extracted_json = result["choices"][0]["message"]["content"]
            extracted_data = json.loads(extracted_json)
            
            return {
                "conversation_id": request.conversation_id,
                "extraction_type": request.extraction_type,
                "extracted_data": extracted_data,
                "transcript_turns": len(transcript),
                "duration_seconds": conv.get("metadata", {}).get("call_duration_secs"),
                "method": "llm"
            }
            
    except Exception as e:
        logger.error(f"Extraction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _get_extraction_prompt(extraction_type: str, transcript: str) -> str:
    """Get the extraction prompt based on type."""
    
    if extraction_type == "appointment":
        return f"""Analyze this conversation transcript and extract appointment booking information.

TRANSCRIPT:
{transcript}

Extract and return JSON with these fields:
{{
    "wants_appointment": true/false (did the user want to book an appointment?),
    "appointment_date": "YYYY-MM-DD" or null (the date mentioned, convert to ISO format),
    "appointment_time": "HH:MM" or null (the time in 24-hour format),
    "purpose": "string" or null (why they want the appointment),
    "customer_name": "string" or null (customer's name if mentioned),
    "appointment_confirmed": true/false (was the appointment confirmed by the agent?),
    "additional_notes": "string" or null (any other relevant details),
    "confidence": 0.0-1.0 (how confident you are in this extraction)
}}

If a field cannot be determined, use null. Be precise with dates and times."""

    elif extraction_type == "lead":
        return f"""Analyze this conversation transcript and extract lead/sales information.

TRANSCRIPT:
{transcript}

Extract and return JSON with these fields:
{{
    "is_interested": true/false,
    "interest_level": "high/medium/low/none",
    "customer_name": "string" or null,
    "email": "string" or null,
    "phone": "string" or null,
    "product_interest": ["list of products mentioned"],
    "objections": ["list of objections raised"],
    "follow_up_needed": true/false,
    "notes": "string",
    "confidence": 0.0-1.0
}}"""

    else:  # support
        return f"""Analyze this conversation transcript and extract support ticket information.

TRANSCRIPT:
{transcript}

Extract and return JSON with these fields:
{{
    "issue_type": "string",
    "issue_description": "string",
    "issue_resolved": true/false,
    "customer_name": "string" or null,
    "customer_sentiment": "positive/neutral/negative",
    "follow_up_needed": true/false,
    "notes": "string",
    "confidence": 0.0-1.0
}}"""


async def _extract_appointment_rules(conversation_id: str, transcript_text: str, transcript: list) -> dict:
    """Fallback rule-based extraction when no LLM available."""
    import re
    from datetime import datetime
    
    text_lower = transcript_text.lower()
    
    # Check if wants appointment
    wants_appointment = any(word in text_lower for word in [
        "book", "schedule", "appointment", "meeting", "yes"
    ])
    
    # Extract date patterns
    date_match = None
    date_patterns = [
        r'(\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?(\w+)(?:\s*,?\s*(\d{4}))?',  # 2nd of February 2026
        r'(\w+)\s+(\d{1,2})(?:st|nd|rd|th)?(?:\s*,?\s*(\d{4}))?',  # February 2nd, 2026
    ]
    
    months = {
        'january': 1, 'february': 2, 'march': 3, 'april': 4,
        'may': 5, 'june': 6, 'july': 7, 'august': 8,
        'september': 9, 'october': 10, 'november': 11, 'december': 12
    }
    
    for pattern in date_patterns:
        match = re.search(pattern, text_lower)
        if match:
            groups = match.groups()
            try:
                if groups[1].lower() in months:  # First pattern
                    day = int(groups[0])
                    month = months[groups[1].lower()]
                    year = int(groups[2]) if groups[2] else datetime.now().year
                else:  # Second pattern
                    month = months.get(groups[0].lower())
                    day = int(groups[1])
                    year = int(groups[2]) if groups[2] else datetime.now().year
                if month:
                    date_match = f"{year:04d}-{month:02d}-{day:02d}"
            except:
                pass
            break
    
    # Extract time
    time_match = None
    time_patterns = [
        r'(\d{1,2})(?::(\d{2}))?\s*(am|pm|a\.m\.|p\.m\.)',  # 3 pm, 3:00 pm
        r'at\s+(\d{1,2})(?::(\d{2}))?',  # at 3
    ]
    
    for pattern in time_patterns:
        match = re.search(pattern, text_lower)
        if match:
            groups = match.groups()
            try:
                hour = int(groups[0])
                minute = int(groups[1]) if groups[1] else 0
                if len(groups) > 2 and groups[2] and 'p' in groups[2].lower() and hour < 12:
                    hour += 12
                time_match = f"{hour:02d}:{minute:02d}"
            except:
                pass
            break
    
    # Extract purpose
    purpose = None
    purpose_keywords = ["purpose", "reason", "for", "about", "discuss", "query", "question"]
    for turn in reversed(transcript):
        msg = (turn.get("message") or turn.get("original_message", "")).lower()
        if turn.get("role") == "user" and any(kw in msg for kw in purpose_keywords):
            purpose = turn.get("message") or turn.get("original_message")
            break
    
    if not purpose:
        # Look for user message after agent asks about purpose
        for i, turn in enumerate(transcript):
            if turn.get("role") == "agent" and "purpose" in (turn.get("message") or "").lower():
                if i + 1 < len(transcript) and transcript[i + 1].get("role") == "user":
                    purpose = transcript[i + 1].get("message") or transcript[i + 1].get("original_message")
                    break
    
    return {
        "conversation_id": conversation_id,
        "extraction_type": "appointment",
        "extracted_data": {
            "wants_appointment": wants_appointment,
            "appointment_date": date_match,
            "appointment_time": time_match,
            "purpose": purpose,
            "customer_name": None,
            "appointment_confirmed": "confirmed" in text_lower or "scheduled" in text_lower,
            "additional_notes": None,
            "confidence": 0.6 if wants_appointment else 0.4
        },
        "transcript_turns": len(transcript),
        "method": "rules"
    }
