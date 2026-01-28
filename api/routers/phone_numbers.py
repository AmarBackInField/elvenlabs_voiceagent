"""
Phone Numbers Router.
Handles phone number import and management endpoints.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from client import ElevenLabsClient
from api.dependencies import get_client
from api.schemas import (
    ImportPhoneNumberRequest,
    ImportSIPTrunkPhoneNumberRequest,
    ImportPhoneNumberResponse,
    PhoneNumberResponse,
    PhoneNumberListResponse,
    UpdatePhoneNumberRequest,
    TwilioOutboundCallRequest,
    TwilioOutboundCallResponse,
    SuccessResponse,
    ErrorResponse
)
from exceptions import ElevenLabsError, NotFoundError

logger = logging.getLogger("elevenlabs.phone_numbers.router")

router = APIRouter(
    prefix="/phone-numbers",
    tags=["Phone Numbers"],
    responses={
        401: {"model": ErrorResponse, "description": "Authentication failed"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)


@router.post(
    "",
    response_model=ImportPhoneNumberResponse,
    status_code=201,
    summary="Import Phone Number (Twilio)",
    description="Import a phone number from Twilio"
)
async def import_phone_number(
    request: ImportPhoneNumberRequest,
    client: ElevenLabsClient = Depends(get_client)
):
    """
    Import a phone number from Twilio.
    
    Requires:
    - phone_number: Number in E.164 format (e.g., +14155551234)
    - label: Display name for the number
    - sid: Twilio Account SID
    - token: Twilio authentication token
    
    For SIP trunk providers, use POST /phone-numbers/sip-trunk instead.
    """
    try:
        result = client.phone_numbers.import_phone_number(
            phone_number=request.phone_number,
            label=request.label,
            sid=request.sid,
            token=request.token
        )
        return ImportPhoneNumberResponse(phone_number_id=result["phone_number_id"])
        
    except ElevenLabsError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@router.post(
    "/sip-trunk",
    response_model=ImportPhoneNumberResponse,
    status_code=201,
    summary="Import Phone Number (SIP Trunk)",
    description="Import a phone number from a SIP trunk provider"
)
async def import_sip_trunk_phone_number(
    request: ImportSIPTrunkPhoneNumberRequest,
    client: ElevenLabsClient = Depends(get_client)
):
    """
    Import a phone number from a SIP trunk provider.
    
    This endpoint is for non-Twilio SIP providers (Vonage, Fibrapro, etc.)
    
    Requires:
    - phone_number: Number in E.164 format (e.g., +390620199287)
    - label: Display name for the number
    - provider: Must be "sip_trunk"
    - outbound_trunk_config: SIP URI and authentication for outbound calls
    - inbound_trunk_config: SIP URI and authentication for inbound calls (optional)
    
    The ElevenLabs inbound SIP endpoint is: sip.rtc.elevenlabs.io:5060
    """
    try:
        # Build the payload for ElevenLabs API
        payload = {
            "phone_number": request.phone_number,
            "label": request.label,
            "provider": "sip_trunk",
            "supports_inbound": request.supports_inbound,
            "supports_outbound": request.supports_outbound
        }
        
        # Add outbound trunk config
        if request.outbound_trunk_config:
            outbound_config = {"sip_uri": request.outbound_trunk_config.sip_uri}
            if request.outbound_trunk_config.authentication:
                outbound_config["authentication"] = {
                    "username": request.outbound_trunk_config.authentication.username,
                    "password": request.outbound_trunk_config.authentication.password
                }
            if request.outbound_trunk_config.codecs:
                outbound_config["codecs"] = request.outbound_trunk_config.codecs
            if request.outbound_trunk_config.dtmf_mode:
                outbound_config["dtmf_mode"] = request.outbound_trunk_config.dtmf_mode
            payload["outbound_trunk_config"] = outbound_config
        
        # Add inbound trunk config
        if request.inbound_trunk_config:
            inbound_config = {"sip_uri": request.inbound_trunk_config.sip_uri}
            if request.inbound_trunk_config.authentication:
                inbound_config["authentication"] = {
                    "username": request.inbound_trunk_config.authentication.username,
                    "password": request.inbound_trunk_config.authentication.password
                }
            if request.inbound_trunk_config.codecs:
                inbound_config["codecs"] = request.inbound_trunk_config.codecs
            if request.inbound_trunk_config.dtmf_mode:
                inbound_config["dtmf_mode"] = request.inbound_trunk_config.dtmf_mode
            payload["inbound_trunk_config"] = inbound_config
        
        logger.info(f"Importing SIP trunk phone number: {request.phone_number}")
        
        # Call ElevenLabs API directly with the SIP trunk payload
        result = client.phone_numbers.import_sip_trunk_phone_number(payload)
        
        return ImportPhoneNumberResponse(phone_number_id=result["phone_number_id"])
        
    except ElevenLabsError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@router.get(
    "",
    response_model=PhoneNumberListResponse,
    summary="List Phone Numbers",
    description="Get a list of all imported phone numbers"
)
async def list_phone_numbers(
    cursor: Optional[str] = Query(None, description="Pagination cursor"),
    page_size: int = Query(30, ge=1, le=100, description="Results per page"),
    client: ElevenLabsClient = Depends(get_client)
):
    """List all imported phone numbers with pagination."""
    try:
        result = client.phone_numbers.list_phone_numbers(cursor=cursor, page_size=page_size)
        return PhoneNumberListResponse(
            phone_numbers=result.get("phone_numbers", []),
            cursor=result.get("cursor")
        )
    except ElevenLabsError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@router.get(
    "/{phone_number_id}",
    response_model=PhoneNumberResponse,
    summary="Get Phone Number",
    description="Get details of a specific phone number",
    responses={404: {"model": ErrorResponse, "description": "Phone number not found"}}
)
async def get_phone_number(
    phone_number_id: str,
    client: ElevenLabsClient = Depends(get_client)
):
    """Get details of a specific phone number by ID."""
    try:
        result = client.phone_numbers.get_phone_number(phone_number_id)
        return PhoneNumberResponse(**result)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ElevenLabsError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@router.patch(
    "/{phone_number_id}",
    response_model=PhoneNumberResponse,
    summary="Update Phone Number",
    description="Update phone number configuration (e.g., assign agent)",
    responses={404: {"model": ErrorResponse, "description": "Phone number not found"}}
)
async def update_phone_number(
    phone_number_id: str,
    request: UpdatePhoneNumberRequest,
    client: ElevenLabsClient = Depends(get_client)
):
    """
    Update a phone number's configuration.
    
    Common use case: Assign an agent to handle incoming calls on this number.
    """
    try:
        update_data = request.model_dump(exclude_none=True)
        result = client.phone_numbers.update_phone_number(phone_number_id, **update_data)
        return PhoneNumberResponse(**result)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ElevenLabsError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@router.delete(
    "/{phone_number_id}",
    response_model=SuccessResponse,
    summary="Delete Phone Number",
    description="Delete an imported phone number",
    responses={404: {"model": ErrorResponse, "description": "Phone number not found"}}
)
async def delete_phone_number(
    phone_number_id: str,
    client: ElevenLabsClient = Depends(get_client)
):
    """Delete a phone number by ID."""
    try:
        client.phone_numbers.delete_phone_number(phone_number_id)
        return SuccessResponse(message=f"Phone number {phone_number_id} deleted successfully")
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ElevenLabsError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@router.post(
    "/twilio/outbound-call",
    response_model=TwilioOutboundCallResponse,
    summary="Outbound Call via Twilio",
    description="Initiate an outbound call using a Twilio phone number"
)
async def twilio_outbound_call(
    request: TwilioOutboundCallRequest,
    client: ElevenLabsClient = Depends(get_client)
):
    """
    Initiate an outbound call via Twilio.
    
    This endpoint is for phone numbers imported from Twilio.
    For SIP trunk numbers, use the /sip-trunk/outbound-call endpoint.
    
    The agent will call the specified number and start a conversation.
    You can inject dynamic variables that will be available in the conversation.
    
    Optionally include ecommerce_credentials to enable product/order lookups during the call.
    
    Example use cases:
    - Appointment reminders
    - Customer outreach with product info
    - Order status calls
    """
    try:
        # Build conversation_initiation_client_data if dynamic_variables or first_message provided
        conversation_data = None
        if request.dynamic_variables or request.first_message:
            conversation_data = {}
            if request.dynamic_variables:
                conversation_data["dynamic_variables"] = request.dynamic_variables
            if request.first_message:
                conversation_data["first_message"] = request.first_message
        
        result = client.phone_numbers.twilio_outbound_call(
            agent_id=request.agent_id,
            agent_phone_number_id=request.agent_phone_number_id,
            to_number=request.to_number,
            conversation_initiation_client_data=conversation_data
        )
        
        # Set up ecommerce client if credentials provided
        ecommerce_enabled = False
        email_enabled = False
        conversation_id = result.get("conversation_id")
        
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
            email_enabled = True
        
        return TwilioOutboundCallResponse(
            success=result.get("success", False),
            message=result.get("message"),
            conversation_id=conversation_id,
            call_sid=result.get("callSid"),
            ecommerce_enabled=ecommerce_enabled
        )
        
    except ElevenLabsError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))
