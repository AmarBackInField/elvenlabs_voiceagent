"""
Email Templates Router.
Handles email template CRUD operations and auto-creates webhook tools.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from api.schemas import (
    CreateEmailTemplateRequest,
    EmailTemplateResponse,
    EmailTemplateListResponse,
    EmailTemplateParameter,
    StoreCustomerSessionRequest,
    SuccessResponse,
    ErrorResponse
)
from email_templates import (
    get_email_template_service,
    set_webhook_base_url,
    customer_sessions,
    EmailTemplate
)


router = APIRouter(
    prefix="/email-templates",
    tags=["Email Templates"],
    responses={
        401: {"model": ErrorResponse, "description": "Authentication failed"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)


def _template_to_response(template: EmailTemplate) -> EmailTemplateResponse:
    """Convert EmailTemplate to response model."""
    return EmailTemplateResponse(
        template_id=template.template_id,
        name=template.name,
        description=template.description,
        subject_template=template.subject_template,
        body_template=template.body_template,
        parameters=[
            EmailTemplateParameter(
                name=p.name,
                description=p.description,
                required=p.required
            ) for p in template.parameters
        ],
        tool_id=template.tool_id,
        created_at=template.created_at,
        sender_email=template.sender_email
    )


@router.post(
    "",
    response_model=EmailTemplateResponse,
    status_code=201,
    summary="Create Email Template",
    description="Create an email template and auto-create corresponding ElevenLabs webhook tool"
)
async def create_email_template(request: CreateEmailTemplateRequest):
    """
    Create an email template with the following placeholders:
    
    - Use {{customer_name}} or {{name}} for customer name (auto-filled from session)
    - Use {{customer_email}} or {{email}} for customer email (auto-filled from session)
    - Use {{date}}, {{time}}, {{notes}}, etc. for parameters the AI will provide
    
    A webhook tool will be automatically created in ElevenLabs that your agent can use.
    """
    try:
        # Set webhook base URL if provided
        if request.webhook_base_url:
            set_webhook_base_url(request.webhook_base_url)
        
        service = get_email_template_service(request.webhook_base_url)
        
        # Convert parameters to dict format
        params = None
        if request.parameters:
            params = [p.model_dump() for p in request.parameters]
        
        template = service.create_template(
            name=request.name,
            description=request.description,
            subject_template=request.subject_template,
            body_template=request.body_template,
            parameters=params,
            auto_create_tool=True,
            sender_email=request.sender_email
        )
        
        return _template_to_response(template)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "",
    response_model=EmailTemplateListResponse,
    summary="List Email Templates",
    description="Get all email templates"
)
async def list_email_templates():
    """List all email templates."""
    try:
        service = get_email_template_service()
        templates = service.list_templates()
        
        return EmailTemplateListResponse(
            templates=[_template_to_response(t) for t in templates],
            count=len(templates)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{template_id}",
    response_model=EmailTemplateResponse,
    summary="Get Email Template",
    description="Get a specific email template by ID",
    responses={404: {"model": ErrorResponse, "description": "Template not found"}}
)
async def get_email_template(template_id: str):
    """Get an email template by ID."""
    try:
        service = get_email_template_service()
        template = service.get_template(template_id)
        
        if not template:
            raise HTTPException(status_code=404, detail=f"Template not found: {template_id}")
        
        return _template_to_response(template)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/{template_id}",
    response_model=SuccessResponse,
    summary="Delete Email Template",
    description="Delete an email template and its associated tool",
    responses={404: {"model": ErrorResponse, "description": "Template not found"}}
)
async def delete_email_template(template_id: str):
    """Delete an email template."""
    try:
        service = get_email_template_service()
        
        if not service.get_template(template_id):
            raise HTTPException(status_code=404, detail=f"Template not found: {template_id}")
        
        service.delete_template(template_id)
        return SuccessResponse(message=f"Template {template_id} deleted successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Customer Session Management
# =============================================================================

@router.post(
    "/sessions",
    response_model=SuccessResponse,
    status_code=201,
    summary="Store Customer Session",
    description="Store customer info for a conversation (used by email webhooks)"
)
async def store_customer_session(request: StoreCustomerSessionRequest):
    """
    Store customer information for a conversation.
    
    This should be called when starting a campaign/call to associate
    customer info (name, email) with the conversation_id.
    """
    try:
        customer_sessions.store(
            conversation_id=request.conversation_id,
            customer_info=request.customer_info.model_dump()
        )
        return SuccessResponse(
            message=f"Customer session stored for conversation {request.conversation_id}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/sessions/{conversation_id}",
    summary="Get Customer Session",
    description="Get customer info for a conversation",
    responses={404: {"model": ErrorResponse, "description": "Session not found"}}
)
async def get_customer_session(conversation_id: str):
    """Get customer session info."""
    session = customer_sessions.get(conversation_id)
    
    if not session:
        raise HTTPException(status_code=404, detail=f"Session not found: {conversation_id}")
    
    return session


@router.delete(
    "/sessions/{conversation_id}",
    response_model=SuccessResponse,
    summary="Delete Customer Session",
    description="Remove customer session info"
)
async def delete_customer_session(conversation_id: str):
    """Delete customer session."""
    customer_sessions.remove(conversation_id)
    return SuccessResponse(message=f"Session {conversation_id} removed")


@router.get(
    "/sessions",
    summary="List All Sessions",
    description="List all active customer sessions (for debugging)"
)
async def list_customer_sessions():
    """List all customer sessions."""
    return customer_sessions.list_all()
