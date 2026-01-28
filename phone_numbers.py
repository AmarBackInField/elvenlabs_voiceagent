"""
Phone Number Service for ElevenLabs API.
Handles phone number import and management operations.
"""

from typing import Optional, Dict, Any

from base import BaseClient
from config import ElevenLabsConfig
from logger import APICallLogger


class PhoneNumberService(BaseClient):
    """
    Service class for managing phone numbers in ElevenLabs.
    
    Provides methods for:
    - Importing phone numbers from Twilio
    - Importing phone numbers via SIP trunk
    - Listing phone numbers
    - Deleting phone numbers
    
    Example:
        >>> from config import ElevenLabsConfig
        >>> config = ElevenLabsConfig.from_env()
        >>> phone_service = PhoneNumberService(config)
        >>> result = phone_service.import_phone_number(
        ...     phone_number="+14155551234",
        ...     label="Main Line",
        ...     sid="twilio_sid",
        ...     token="twilio_token"
        ... )
    """
    
    # API Endpoints
    PHONE_NUMBERS_ENDPOINT = "/v1/convai/phone-numbers"
    TWILIO_OUTBOUND_CALL_ENDPOINT = "/v1/convai/twilio/outbound-call"
    
    def __init__(self, config: ElevenLabsConfig):
        """
        Initialize Phone Number Service.
        
        Args:
            config: ElevenLabsConfig instance
        """
        super().__init__(config, logger_name="elevenlabs.phone_numbers")
        self.logger.info("PhoneNumberService initialized")
    
    def import_phone_number(
        self,
        phone_number: str,
        label: str,
        sid: str,
        token: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Import a phone number from provider configuration (Twilio or SIP trunk).
        
        API Endpoint: POST /v1/convai/phone-numbers
        
        Args:
            phone_number: Phone number in E.164 format (e.g., "+14155551234")
            label: Label/name for the phone number
            sid: Provider SID (Twilio Account SID or SIP trunk ID)
            token: Provider authentication token
            **kwargs: Additional configuration options
            
        Returns:
            Response containing phone_number_id
            
        Example:
            >>> result = service.import_phone_number(
            ...     phone_number="+14155551234",
            ...     label="Customer Support Line",
            ...     sid="AC1234567890abcdef",
            ...     token="your_auth_token"
            ... )
            >>> print(result["phone_number_id"])
        """
        with APICallLogger(self.logger, "Import Phone Number", phone_number=phone_number):
            payload = {
                "phone_number": phone_number,
                "label": label,
                "sid": sid,
                "token": token
            }
            
            payload.update(kwargs)
            
            response = self._make_request(
                method="POST",
                endpoint=self.PHONE_NUMBERS_ENDPOINT,
                data=payload
            )
            
            phone_id = response.get("phone_number_id", "unknown")
            self.logger.info(f"Phone number imported: {phone_id}")
            return response
    
    def get_phone_number(self, phone_number_id: str) -> Dict[str, Any]:
        """
        Get details of a specific phone number.
        
        API Endpoint: GET /v1/convai/phone-numbers/{phone_number_id}
        
        Args:
            phone_number_id: Phone number identifier
            
        Returns:
            Phone number details
            
        Raises:
            NotFoundError: If phone number doesn't exist
        """
        with APICallLogger(self.logger, "Get Phone Number", phone_number_id=phone_number_id):
            response = self._make_request(
                method="GET",
                endpoint=f"{self.PHONE_NUMBERS_ENDPOINT}/{phone_number_id}"
            )
            
            self.logger.info(f"Retrieved phone number: {phone_number_id}")
            return response
    
    def list_phone_numbers(
        self,
        cursor: Optional[str] = None,
        page_size: int = 30
    ) -> Dict[str, Any]:
        """
        List all imported phone numbers.
        
        API Endpoint: GET /v1/convai/phone-numbers
        
        Args:
            cursor: Pagination cursor
            page_size: Results per page
            
        Returns:
            List of phone numbers with pagination
        """
        with APICallLogger(self.logger, "List Phone Numbers"):
            params = {"page_size": page_size}
            if cursor:
                params["cursor"] = cursor
            
            response = self._make_request(
                method="GET",
                endpoint=self.PHONE_NUMBERS_ENDPOINT,
                params=params
            )
            
            count = len(response.get("phone_numbers", []))
            self.logger.info(f"Retrieved {count} phone numbers")
            return response
    
    def update_phone_number(
        self,
        phone_number_id: str,
        agent_id: Optional[str] = None,
        label: Optional[str] = None,
        **updates
    ) -> Dict[str, Any]:
        """
        Update a phone number configuration.
        
        API Endpoint: PATCH /v1/convai/phone-numbers/{phone_number_id}
        
        Args:
            phone_number_id: Phone number ID to update
            agent_id: Agent ID to assign to this phone number
            label: New label for the phone number
            **updates: Additional fields to update
            
        Returns:
            Updated phone number details
        """
        with APICallLogger(self.logger, "Update Phone Number", phone_number_id=phone_number_id):
            payload = {}
            
            if agent_id is not None:
                payload["agent_id"] = agent_id
            if label is not None:
                payload["label"] = label
            
            payload.update(updates)
            
            response = self._make_request(
                method="PATCH",
                endpoint=f"{self.PHONE_NUMBERS_ENDPOINT}/{phone_number_id}",
                data=payload
            )
            
            self.logger.info(f"Phone number updated: {phone_number_id}")
            return response
    
    def delete_phone_number(self, phone_number_id: str) -> Dict[str, Any]:
        """
        Delete a phone number.
        
        API Endpoint: DELETE /v1/convai/phone-numbers/{phone_number_id}
        
        Args:
            phone_number_id: Phone number ID to delete
            
        Returns:
            Deletion confirmation
        """
        with APICallLogger(self.logger, "Delete Phone Number", phone_number_id=phone_number_id):
            response = self._make_request(
                method="DELETE",
                endpoint=f"{self.PHONE_NUMBERS_ENDPOINT}/{phone_number_id}"
            )
            
            self.logger.info(f"Phone number deleted: {phone_number_id}")
            return response
    
    def twilio_outbound_call(
        self,
        agent_id: str,
        agent_phone_number_id: str,
        to_number: str,
        conversation_initiation_client_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Initiate an outbound call via Twilio.
        
        API Endpoint: POST /v1/convai/twilio/outbound-call
        
        This endpoint is specifically for phone numbers imported from Twilio.
        For SIP trunk numbers, use the SIP trunk outbound call endpoint.
        
        Args:
            agent_id: ID of the agent to handle the call
            agent_phone_number_id: ID of the Twilio phone number to use as caller ID
            to_number: Destination phone number (E.164 format)
            conversation_initiation_client_data: Optional data for personalizing the conversation
                Can include dynamic_variables, custom_llm_extra_body, etc.
            **kwargs: Additional call configuration options
            
        Returns:
            Response containing:
            - success: Boolean indicating call initiation success
            - message: Status message
            - conversation_id: ID of the conversation (if successful)
            - callSid: Twilio call SID (if successful)
            
        Example:
            >>> call = service.twilio_outbound_call(
            ...     agent_id="agent_abc123",
            ...     agent_phone_number_id="phnum_xyz789",
            ...     to_number="+14155551234",
            ...     conversation_initiation_client_data={
            ...         "dynamic_variables": {
            ...             "customer_name": "John Doe",
            ...             "order_id": "ORD-12345"
            ...         }
            ...     }
            ... )
            >>> if call["success"]:
            ...     print(f"Call started: {call['conversation_id']}")
        """
        with APICallLogger(self.logger, "Twilio Outbound Call",
                          agent_id=agent_id, to_number=to_number):
            payload = {
                "agent_id": agent_id,
                "agent_phone_number_id": agent_phone_number_id,
                "to_number": to_number
            }
            
            if conversation_initiation_client_data is not None:
                payload["conversation_initiation_client_data"] = conversation_initiation_client_data
            
            payload.update(kwargs)
            
            response = self._make_request(
                method="POST",
                endpoint=self.TWILIO_OUTBOUND_CALL_ENDPOINT,
                data=payload
            )
            
            success = response.get("success", False)
            conv_id = response.get("conversation_id", "unknown")
            
            if success:
                self.logger.info(f"Twilio outbound call initiated: {conv_id}")
            else:
                self.logger.warning(f"Twilio outbound call failed: {response.get('message', 'Unknown error')}")
            
            return response
