"""
SIP Trunk Router.
Handles SIP trunk configuration and outbound call endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException

from client import ElevenLabsClient
from api.dependencies import get_client
from api.schemas import (
    OutboundCallRequest,
    OutboundCallResponse,
    CreateSIPTrunkRequest,
    SIPTrunkResponse,
    SIPTrunkListResponse,
    SuccessResponse,
    ErrorResponse
)
from exceptions import ElevenLabsError, NotFoundError


router = APIRouter(
    prefix="/sip-trunk",
    tags=["SIP Trunk"],
    responses={
        401: {"model": ErrorResponse, "description": "Authentication failed"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)


@router.post(
    "/outbound-call",
    response_model=OutboundCallResponse,
    summary="Outbound Call via SIP",
    description="Initiate an outbound call via SIP trunk"
)
async def outbound_call(
    request: OutboundCallRequest,
    client: ElevenLabsClient = Depends(get_client)
):
    """
    Initiate an outbound call via SIP trunk.
    
    The agent will call the specified number and start a conversation.
    You can inject dynamic variables that will be available in the conversation.
    
    Features:
    - Include ecommerce_credentials to enable product/order lookups during the call
    - Include customer_info to enable email templates during the call
    - Include sender_email for the business/sender email header
    
    Example use cases:
    - Appointment reminders with email confirmation
    - Customer outreach with product info
    - Follow-up calls with order status
    """
    try:
        result = client.sip_trunk.outbound_call(
            agent_id=request.agent_id,
            agent_phone_number_id=request.agent_phone_number_id,
            to_number=request.to_number,
            custom_llm_extra_body=request.custom_llm_extra_body,
            dynamic_variables=request.dynamic_variables,
            first_message=request.first_message
        )
        
        conversation_id = result.get("conversation_id")
        ecommerce_enabled = False
        
        # Store ecommerce credentials for webhook lookups if provided
        if request.ecommerce_credentials and conversation_id:
            from ecommerce import get_ecommerce_service
            ecommerce_service = get_ecommerce_service()
            ecommerce_service.create_client(
                session_id=conversation_id,
                platform=request.ecommerce_credentials.platform,
                base_url=request.ecommerce_credentials.base_url,
                api_key=request.ecommerce_credentials.api_key,
                api_secret=request.ecommerce_credentials.api_secret,
                access_token=request.ecommerce_credentials.access_token
            )
            ecommerce_enabled = True
        
        # Store customer info for email tools if provided
        if request.customer_info and conversation_id:
            from email_templates import customer_sessions
            customer_data = request.customer_info.model_dump()
            # Include sender_email if provided
            if request.sender_email:
                customer_data["sender_email"] = request.sender_email
            customer_sessions.store(
                conversation_id=conversation_id,
                customer_info=customer_data
            )
        
        return OutboundCallResponse(
            success=result.get("success", False),
            message=result.get("message"),
            conversation_id=conversation_id,
            sip_call_id=result.get("sip_call_id")
        )
        
    except ElevenLabsError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@router.post(
    "",
    response_model=SIPTrunkResponse,
    status_code=201,
    summary="Create SIP Trunk",
    description="Create a new SIP trunk configuration"
)
async def create_sip_trunk(
    request: CreateSIPTrunkRequest,
    client: ElevenLabsClient = Depends(get_client)
):
    """Create a new SIP trunk configuration."""
    try:
        extra_data = request.model_dump(exclude={"name", "sip_uri", "authentication"}, exclude_none=True)
        
        result = client.sip_trunk.create_sip_trunk(
            name=request.name,
            sip_uri=request.sip_uri,
            authentication=request.authentication,
            **extra_data
        )
        return SIPTrunkResponse(**result)
        
    except ElevenLabsError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@router.get(
    "",
    response_model=SIPTrunkListResponse,
    summary="List SIP Trunks",
    description="Get a list of all SIP trunk configurations"
)
async def list_sip_trunks(
    client: ElevenLabsClient = Depends(get_client)
):
    """List all SIP trunk configurations."""
    try:
        result = client.sip_trunk.list_sip_trunks()
        return SIPTrunkListResponse(sip_trunks=result.get("sip_trunks", []))
    except ElevenLabsError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@router.get(
    "/{sip_trunk_id}",
    response_model=SIPTrunkResponse,
    summary="Get SIP Trunk",
    description="Get details of a specific SIP trunk",
    responses={404: {"model": ErrorResponse, "description": "SIP trunk not found"}}
)
async def get_sip_trunk(
    sip_trunk_id: str,
    client: ElevenLabsClient = Depends(get_client)
):
    """Get details of a specific SIP trunk by ID."""
    try:
        result = client.sip_trunk.get_sip_trunk(sip_trunk_id)
        return SIPTrunkResponse(**result)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ElevenLabsError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@router.delete(
    "/{sip_trunk_id}",
    response_model=SuccessResponse,
    summary="Delete SIP Trunk",
    description="Delete a SIP trunk configuration",
    responses={404: {"model": ErrorResponse, "description": "SIP trunk not found"}}
)
async def delete_sip_trunk(
    sip_trunk_id: str,
    client: ElevenLabsClient = Depends(get_client)
):
    """Delete a SIP trunk by ID."""
    try:
        client.sip_trunk.delete_sip_trunk(sip_trunk_id)
        return SuccessResponse(message=f"SIP trunk {sip_trunk_id} deleted successfully")
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ElevenLabsError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))
