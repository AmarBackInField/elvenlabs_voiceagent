"""
SIP Trunk Service for ElevenLabs API.
Handles SIP trunk configuration and outbound calls.
"""

from typing import Optional, Dict, Any

from base import BaseClient
from config import ElevenLabsConfig
from logger import APICallLogger


class SIPTrunkService(BaseClient):
    """
    Service class for SIP trunk operations in ElevenLabs.
    
    Provides methods for:
    - Making outbound calls via SIP trunk
    - Managing SIP trunk configurations
    
    Example:
        >>> from config import ElevenLabsConfig
        >>> config = ElevenLabsConfig.from_env()
        >>> sip_service = SIPTrunkService(config)
        >>> call = sip_service.outbound_call(
        ...     agent_id="agent_123",
        ...     agent_phone_number_id="phone_456",
        ...     to_number="+14155551234"
        ... )
    """
    
    # API Endpoints
    SIP_TRUNK_ENDPOINT = "/v1/convai/sip-trunk"
    OUTBOUND_CALL_ENDPOINT = "/v1/convai/sip-trunk/outbound-call"
    
    def __init__(self, config: ElevenLabsConfig):
        """
        Initialize SIP Trunk Service.
        
        Args:
            config: ElevenLabsConfig instance
        """
        super().__init__(config, logger_name="elevenlabs.sip_trunk")
        self.logger.info("SIPTrunkService initialized")
    
    def outbound_call(
        self,
        agent_id: str,
        agent_phone_number_id: str,
        to_number: str,
        custom_llm_extra_body: Optional[Dict[str, Any]] = None,
        dynamic_variables: Optional[Dict[str, str]] = None,
        first_message: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Initiate an outbound call via SIP trunk.
        
        API Endpoint: POST /v1/convai/sip-trunk/outbound-call
        
        Args:
            agent_id: ID of the agent to handle the call
            agent_phone_number_id: ID of the phone number to use as caller ID
            to_number: Destination phone number (E.164 format)
            custom_llm_extra_body: Extra data to pass to custom LLM
            dynamic_variables: Variables to inject into the conversation
            first_message: Override the agent's default first message
            **kwargs: Additional call configuration options
            
        Returns:
            Response containing:
            - success: Boolean indicating call initiation success
            - message: Status message
            - conversation_id: ID of the conversation
            - sip_call_id: SIP call identifier
            
        Example:
            >>> call = service.outbound_call(
            ...     agent_id="J3Pbu5gP6NNKBscdCdwB",
            ...     agent_phone_number_id="ph_abc123",
            ...     to_number="+14155551234",
            ...     dynamic_variables={
            ...         "customer_name": "John Doe",
            ...         "order_id": "ORD-12345"
            ...     }
            ... )
            >>> if call["success"]:
            ...     print(f"Call started: {call['conversation_id']}")
        """
        with APICallLogger(self.logger, "Outbound Call via SIP",
                          agent_id=agent_id, to_number=to_number):
            payload = {
                "agent_id": agent_id,
                "agent_phone_number_id": agent_phone_number_id,
                "to_number": to_number
            }
            
            if custom_llm_extra_body is not None:
                payload["custom_llm_extra_body"] = custom_llm_extra_body
            
            if dynamic_variables is not None:
                payload["dynamic_variables"] = dynamic_variables
            
            if first_message is not None:
                payload["first_message"] = first_message
            
            payload.update(kwargs)
            
            response = self._make_request(
                method="POST",
                endpoint=self.OUTBOUND_CALL_ENDPOINT,
                data=payload
            )
            
            success = response.get("success", False)
            conv_id = response.get("conversation_id", "unknown")
            
            if success:
                self.logger.info(f"Outbound call initiated: {conv_id}")
            else:
                self.logger.warning(f"Outbound call failed: {response.get('message', 'Unknown error')}")
            
            return response
    
    def get_sip_trunk(self, sip_trunk_id: str) -> Dict[str, Any]:
        """
        Get details of a SIP trunk configuration.
        
        Args:
            sip_trunk_id: SIP trunk identifier
            
        Returns:
            SIP trunk configuration details
        """
        with APICallLogger(self.logger, "Get SIP Trunk", sip_trunk_id=sip_trunk_id):
            response = self._make_request(
                method="GET",
                endpoint=f"{self.SIP_TRUNK_ENDPOINT}/{sip_trunk_id}"
            )
            
            self.logger.info(f"Retrieved SIP trunk: {sip_trunk_id}")
            return response
    
    def list_sip_trunks(self) -> Dict[str, Any]:
        """
        List all SIP trunk configurations.
        
        Returns:
            List of SIP trunk configurations
        """
        with APICallLogger(self.logger, "List SIP Trunks"):
            response = self._make_request(
                method="GET",
                endpoint=self.SIP_TRUNK_ENDPOINT
            )
            
            count = len(response.get("sip_trunks", []))
            self.logger.info(f"Retrieved {count} SIP trunks")
            return response
    
    def create_sip_trunk(
        self,
        name: str,
        sip_uri: str,
        authentication: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a new SIP trunk configuration.
        
        Args:
            name: Name for the SIP trunk
            sip_uri: SIP URI for the trunk
            authentication: Authentication credentials
            **kwargs: Additional configuration options
            
        Returns:
            Created SIP trunk details
        """
        with APICallLogger(self.logger, "Create SIP Trunk", name=name):
            payload = {
                "name": name,
                "sip_uri": sip_uri
            }
            
            if authentication:
                payload["authentication"] = authentication
            
            payload.update(kwargs)
            
            response = self._make_request(
                method="POST",
                endpoint=self.SIP_TRUNK_ENDPOINT,
                data=payload
            )
            
            trunk_id = response.get("sip_trunk_id", "unknown")
            self.logger.info(f"SIP trunk created: {trunk_id}")
            return response
    
    def delete_sip_trunk(self, sip_trunk_id: str) -> Dict[str, Any]:
        """
        Delete a SIP trunk configuration.
        
        Args:
            sip_trunk_id: SIP trunk ID to delete
            
        Returns:
            Deletion confirmation
        """
        with APICallLogger(self.logger, "Delete SIP Trunk", sip_trunk_id=sip_trunk_id):
            response = self._make_request(
                method="DELETE",
                endpoint=f"{self.SIP_TRUNK_ENDPOINT}/{sip_trunk_id}"
            )
            
            self.logger.info(f"SIP trunk deleted: {sip_trunk_id}")
            return response
