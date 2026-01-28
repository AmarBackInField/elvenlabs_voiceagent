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
    prefix="/webhook",
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
        
        limit = body.get("limit", 5)
        if isinstance(limit, str):
            limit = int(limit)
        limit = min(max(limit, 1), 20)
        
        if not conversation_id:
            logger.warning("No conversation_id in webhook request")
            return WebhookResponse(
                success=False,
                error="No ecommerce platform connected. Please provide store credentials when starting the call."
            )
        
        # Get products from ecommerce service
        ecommerce_service = get_ecommerce_service()
        
        # Debug logging
        logger.info(f"Looking up ecommerce client for conversation_id: {conversation_id}")
        client = ecommerce_service.get_client(conversation_id)
        if client:
            logger.info(f"Found client: platform={client.platform}, base_url={client.base_url}")
        else:
            logger.warning(f"No client found for conversation_id: {conversation_id}")
            logger.info(f"Active sessions: {list(ecommerce_service._clients.keys())}")
        
        result = ecommerce_service.get_products(session_id=conversation_id, limit=limit)
        
        if result.get("success"):
            formatted = result.get("formatted", "No products found.")
            logger.info(f"Products fetched successfully for conversation {conversation_id}")
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
        
        limit = body.get("limit", 5)
        if isinstance(limit, str):
            limit = int(limit)
        limit = min(max(limit, 1), 20)
        
        if not conversation_id:
            logger.warning("No conversation_id in webhook request")
            return WebhookResponse(
                success=False,
                error="No ecommerce platform connected. Please provide store credentials when starting the call."
            )
        
        # Get orders from ecommerce service
        ecommerce_service = get_ecommerce_service()
        result = ecommerce_service.get_orders(session_id=conversation_id, limit=limit)
        
        if result.get("success"):
            formatted = result.get("formatted", "No orders found.")
            logger.info(f"Orders fetched successfully for conversation {conversation_id}")
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
    2. Looks up customer info from the session store
    3. Fills the email template with parameters
    4. Sends the email via external API
    """
    from email_templates import get_email_template_service, customer_sessions
    
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
        
        if not conversation_id:
            logger.warning("No conversation_id in email webhook request")
            return WebhookResponse(
                success=False,
                data="Missing conversation_id in request"
            )
        
        # Get customer info from session
        customer_info = customer_sessions.get(conversation_id)
        
        if not customer_info:
            logger.warning(f"No customer session found for conversation {conversation_id}")
            return WebhookResponse(
                success=False,
                data=f"No customer info found for conversation {conversation_id}. Please store customer session first."
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
        parameters = {
            k: v for k, v in body.items() 
            if k not in ["conversation_id", "conversationId", "session_id", "call_id"]
        }
        
        # Get sender_email from customer_info (set during call initiation)
        sender_email = customer_info.get("sender_email", "amarc8399@gmail.com")
        
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
                data=f"Email sent successfully to {customer_info.get('email')}"
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
