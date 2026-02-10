"""
Webhooks Router.
Handles incoming webhook calls from ElevenLabs agents during conversations.
These endpoints are called by ElevenLabs when agents use custom tools.
"""

import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from ecommerce import get_ecommerce_service

logger = logging.getLogger("elevenlabs.webhooks")


router = APIRouter(
    prefix="/webhooks",
    tags=["Webhooks (Agent Tools)"]
)


class WebhookRequest(BaseModel):
    """Base webhook request from ElevenLabs."""
    conversation_id: Optional[str] = None
    agent_id: Optional[str] = None
    # Tool parameters
    limit: Optional[int] = Field(5, ge=1, le=20)
    
    class Config:
        extra = "allow"


class WebhookResponse(BaseModel):
    """Response format for webhook tools."""
    success: bool = True
    data: Optional[str] = None
    error: Optional[str] = None


@router.post(
    "/ecommerce/products",
    response_model=WebhookResponse,
    summary="Get Products (Agent Tool)",
    description="Webhook endpoint for agents to fetch products during calls"
)
async def webhook_get_products(request: Request):
    """
    Webhook called by ElevenLabs agent to fetch products.
    
    The agent will call this when user asks about products, inventory, etc.
    Returns product information as text that the agent can read to the user.
    
    Supports both single calls (with conversation_id) and batch calls (looks up by agent_id).
    """
    try:
        # Parse the request body
        body = await request.json()
        logger.info(f"Webhook get_products called with: {body}")
        
        # Extract conversation_id from various possible locations
        conversation_id = (
            body.get("conversation_id") or 
            body.get("conversationId") or
            body.get("session_id") or
            body.get("call_id")
        )
        
        # Extract agent_id for batch call lookups
        agent_id = body.get("agent_id") or body.get("agentId")
        
        limit = body.get("limit", 5)
        if isinstance(limit, str):
            limit = int(limit)
        limit = min(max(limit, 1), 20)
        
        # Get ecommerce service
        ecommerce_service = get_ecommerce_service()
        
        # Try to get client by conversation_id first
        client = None
        if conversation_id:
            client = ecommerce_service.get_client(conversation_id)
            logger.info(f"Looking up ecommerce client for conversation_id: {conversation_id}")
        
        # If no client found, try batch job context by agent_id
        if not client and agent_id:
            from ecommerce import get_batch_job_context
            batch_context = get_batch_job_context()
            ecom_creds = batch_context.get_ecommerce_credentials(agent_id)
            
            if ecom_creds:
                logger.info(f"Found batch job ecommerce credentials for agent_id: {agent_id}")
                # Create client for this conversation using batch job credentials
                session_key = conversation_id or f"batch_{agent_id}"
                client = ecommerce_service.create_client(
                    session_id=session_key,
                    platform=ecom_creds.get("platform"),
                    base_url=ecom_creds.get("base_url"),
                    api_key=ecom_creds.get("api_key"),
                    api_secret=ecom_creds.get("api_secret"),
                    access_token=ecom_creds.get("access_token")
                )
        
        if not client:
            logger.warning(f"No ecommerce client found for conversation_id={conversation_id}, agent_id={agent_id}")
            return WebhookResponse(
                success=False,
                error="No ecommerce platform connected. Please provide store credentials when starting the call or batch job."
            )
        
        logger.info(f"Found client: platform={client.platform}, base_url={client.base_url}")
        result = client.get_products(limit=limit)
        
        if result.get("success"):
            formatted = result.get("formatted", "No products found.")
            logger.info(f"Products fetched successfully")
            return WebhookResponse(success=True, data=formatted)
        else:
            error = result.get("error", "Failed to fetch products")
            logger.error(f"Failed to fetch products: {error}")
            return WebhookResponse(
                success=False,
                error=f"Could not fetch products: {error}"
            )
            
    except Exception as e:
        logger.error(f"Error in webhook_get_products: {e}")
        return WebhookResponse(
            success=False,
            error=f"Error fetching products: {str(e)}"
        )


@router.post(
    "/ecommerce/orders",
    response_model=WebhookResponse,
    summary="Get Orders (Agent Tool)",
    description="Webhook endpoint for agents to fetch orders during calls"
)
async def webhook_get_orders(request: Request):
    """
    Webhook called by ElevenLabs agent to fetch orders.
    
    The agent will call this when user asks about orders, order status, etc.
    Returns order information as text that the agent can read to the user.
    
    Supports both single calls (with conversation_id) and batch calls (looks up by agent_id).
    """
    try:
        # Parse the request body
        body = await request.json()
        logger.info(f"Webhook get_orders called with: {body}")
        
        # Extract conversation_id from various possible locations
        conversation_id = (
            body.get("conversation_id") or 
            body.get("conversationId") or
            body.get("session_id") or
            body.get("call_id")
        )
        
        # Extract agent_id for batch call lookups
        agent_id = body.get("agent_id") or body.get("agentId")
        
        limit = body.get("limit", 5)
        if isinstance(limit, str):
            limit = int(limit)
        limit = min(max(limit, 1), 20)
        
        # Get ecommerce service
        ecommerce_service = get_ecommerce_service()
        
        # Try to get client by conversation_id first
        client = None
        if conversation_id:
            client = ecommerce_service.get_client(conversation_id)
            logger.info(f"Looking up ecommerce client for conversation_id: {conversation_id}")
        
        # If no client found, try batch job context by agent_id
        if not client and agent_id:
            from ecommerce import get_batch_job_context
            batch_context = get_batch_job_context()
            ecom_creds = batch_context.get_ecommerce_credentials(agent_id)
            
            if ecom_creds:
                logger.info(f"Found batch job ecommerce credentials for agent_id: {agent_id}")
                # Create client for this conversation using batch job credentials
                session_key = conversation_id or f"batch_{agent_id}"
                client = ecommerce_service.create_client(
                    session_id=session_key,
                    platform=ecom_creds.get("platform"),
                    base_url=ecom_creds.get("base_url"),
                    api_key=ecom_creds.get("api_key"),
                    api_secret=ecom_creds.get("api_secret"),
                    access_token=ecom_creds.get("access_token")
                )
        
        if not client:
            logger.warning(f"No ecommerce client found for conversation_id={conversation_id}, agent_id={agent_id}")
            return WebhookResponse(
                success=False,
                error="No ecommerce platform connected. Please provide store credentials when starting the call or batch job."
            )
        
        logger.info(f"Found client: platform={client.platform}, base_url={client.base_url}")
        result = client.get_orders(limit=limit)
        
        if result.get("success"):
            formatted = result.get("formatted", "No orders found.")
            logger.info(f"Orders fetched successfully")
            return WebhookResponse(success=True, data=formatted)
        else:
            error = result.get("error", "Failed to fetch orders")
            logger.error(f"Failed to fetch orders: {error}")
            return WebhookResponse(
                success=False,
                error=f"Could not fetch orders: {error}"
            )
            
    except Exception as e:
        logger.error(f"Error in webhook_get_orders: {e}")
        return WebhookResponse(
            success=False,
            error=f"Error fetching orders: {str(e)}"
        )


@router.post(
    "/test",
    response_model=WebhookResponse,
    summary="Test Webhook",
    description="Test endpoint to verify webhook connectivity"
)
async def webhook_test(request: Request):
    """Test webhook endpoint - returns the received payload."""
    try:
        body = await request.json()
        logger.info(f"Test webhook called with: {body}")
        return WebhookResponse(
            success=True,
            data=f"Webhook received successfully. Payload: {body}"
        )
    except Exception as e:
        return WebhookResponse(
            success=True,
            data=f"Webhook received (no JSON body): {str(e)}"
        )


# =============================================================================
# Email Webhook
# =============================================================================

@router.post(
    "/email/{template_id}",
    response_model=WebhookResponse,
    summary="Email Webhook",
    description="Webhook endpoint for sending emails via email templates"
)
async def email_webhook(template_id: str, request: Request):
    """
    Webhook endpoint called by ElevenLabs when agent wants to send an email.
    
    This endpoint:
    1. Receives the tool call with conversation_id and parameters
    2. Looks up customer info from the session store or batch job context
    3. Fills the email template with parameters
    4. Sends the email via external API
    
    Supports both single calls and batch calls.
    """
    from email_templates import get_email_template_service, customer_sessions
    from ecommerce import get_batch_job_context
    
    try:
        body = await request.json()
        logger.info(f"Email webhook called for template {template_id}: {body}")
        
        # Extract conversation_id
        conversation_id = (
            body.get("conversation_id") or 
            body.get("conversationId") or 
            body.get("session_id") or
            body.get("call_id")
        )
        
        # Extract agent_id and phone number for batch job lookup
        agent_id = body.get("agent_id") or body.get("agentId")
        to_phone = (
            body.get("called_number") or  # From system__called_number dynamic variable
            body.get("to_number") or 
            body.get("phone_number") or 
            body.get("recipient_phone")
        )
        
        logger.info(f"Email webhook lookup: conversation_id={conversation_id}, agent_id={agent_id}, to_phone={to_phone}")
        
        # Try to get customer info from session store first
        customer_info = None
        sender_email = None
        
        if conversation_id:
            customer_info = customer_sessions.get(conversation_id)
        
        # If no customer info found, try batch job context
        if not customer_info:
            batch_context = get_batch_job_context()
            
            # Try lookup by phone number first (most specific)
            if to_phone:
                recipient_info = batch_context.get_recipient_by_phone(to_phone)
                if recipient_info:
                    customer_info = {
                        "name": recipient_info.get("name"),
                        "email": recipient_info.get("email")
                    }
                    # Get sender email from the job
                    job_agent_id = recipient_info.get("agent_id")
                    if job_agent_id:
                        sender_email = batch_context.get_sender_email(job_agent_id)
                    logger.info(f"Found customer info from batch job by phone: {to_phone}")
            
            # Try lookup by agent_id if still no customer info
            if not customer_info and agent_id:
                job = batch_context.get_job_by_agent(agent_id)
                if job:
                    sender_email = job.get("sender_email")
                    logger.info(f"Found batch job context for agent_id: {agent_id}")
        else:
            sender_email = customer_info.get("sender_email")
        
        # If still no customer_info, try to extract from request body parameters
        # This handles inbound calls where user dictates their email during the conversation
        if not customer_info:
            # Look for email in various possible field names
            user_email = (
                body.get("email") or
                body.get("customer_email") or
                body.get("user_email") or
                body.get("recipient_email")
            )
            # Look for name in various possible field names
            user_name = (
                body.get("name") or
                body.get("customer_name") or
                body.get("user_name") or
                body.get("recipient_name")
            )
            
            if user_email:
                customer_info = {
                    "name": user_name or "Customer",
                    "email": user_email
                }
                logger.info(f"Built customer_info from request body: email={user_email}, name={user_name}")
        
        # Resolve dynamic variable names when LLM passes e.g. "customer_email" instead of actual email
        if customer_info:
            dyn_vars = customer_info.get("dynamic_variables") or {}
            email_val = customer_info.get("email") or customer_info.get("customer_email")
            if email_val and "@" not in str(email_val).strip():
                resolved = dyn_vars.get(email_val)
                if resolved:
                    customer_info["email"] = resolved
                    logger.info(f"Resolved email from dynamic variable {email_val!r} to {resolved!r}")
                else:
                    logger.warning(f"Email looks like variable name ({email_val}) but could not resolve.")
                    return WebhookResponse(
                        success=False,
                        data=f"Email parameter is the variable name '{email_val}', not an actual address. Start the outbound call from this server so the session can resolve it, or ensure the agent passes the actual email."
                    )
        
        if not customer_info:
            logger.warning(f"No customer info found for conversation_id={conversation_id}, agent_id={agent_id}, phone={to_phone}")
            return WebhookResponse(
                success=False,
                data=f"No customer info found. Please provide email parameter in the tool call, customer_info when starting the call, or include email in batch recipients."
            )
        
        # Verify we have an email address
        customer_email = customer_info.get("email") or customer_info.get("customer_email")
        if not customer_email:
            logger.warning(f"No email address in customer info: {customer_info}")
            return WebhookResponse(
                success=False,
                data="No email address found for this customer. Please include email in recipient info."
            )
        
        # Get email template service
        service = get_email_template_service()
        template = service.get_template(template_id)
        
        if not template:
            logger.error(f"Template not found: {template_id}")
            return WebhookResponse(
                success=False,
                data=f"Email template not found: {template_id}"
            )
        
        # Extract parameters (exclude known fields)
        exclude_fields = [
            "conversation_id", "conversationId", "session_id", "call_id",
            "agent_id", "agentId", "to_number", "phone_number", "recipient_phone"
        ]
        parameters = {
            k: v for k, v in body.items() 
            if k not in exclude_fields
        }
        
        # Default sender email: call/session/batch first, then template default (for inbound), then global fallback
        if not sender_email and getattr(template, "sender_email", None):
            sender_email = template.sender_email
        if not sender_email:
            sender_email = "amarc8399@gmail.com"
        
        # Send the email
        result = service.send_email(
            template_id=template_id,
            customer_info=customer_info,
            parameters=parameters,
            user_email=sender_email
        )
        
        if result.get("success"):
            return WebhookResponse(
                success=True,
                data=f"Email sent successfully to {customer_email}"
            )
        else:
            return WebhookResponse(
                success=False,
                data=f"Failed to send email: {result.get('error')}"
            )
        
    except Exception as e:
        logger.exception(f"Error in email webhook: {e}")
        return WebhookResponse(
            success=False,
            data=f"Error sending email: {str(e)}"
        )
