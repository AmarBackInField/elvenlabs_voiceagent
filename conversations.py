"""
Conversation Service for ElevenLabs API.
Handles conversation history, transcripts, and recordings.
"""

from typing import Optional, Dict, Any

from base import BaseClient
from config import ElevenLabsConfig
from logger import APICallLogger


class ConversationService(BaseClient):
    """
    Service class for managing ElevenLabs conversation data.
    
    Provides methods for:
    - Getting conversation details and transcripts
    - Getting conversation audio/recordings
    - Listing conversations
    
    Example:
        >>> from config import ElevenLabsConfig
        >>> config = ElevenLabsConfig.from_env()
        >>> conv_service = ConversationService(config)
        >>> details = conv_service.get_conversation("conv_abc123")
        >>> print(details["transcript"])
    """
    
    # API Endpoints
    CONVERSATIONS_ENDPOINT = "/v1/convai/conversations"
    
    def __init__(self, config: ElevenLabsConfig):
        """
        Initialize Conversation Service.
        
        Args:
            config: ElevenLabsConfig instance
        """
        super().__init__(config, logger_name="elevenlabs.conversations")
        self.logger.info("ConversationService initialized")
    
    def get_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """
        Get details of a specific conversation including transcript.
        
        API Endpoint: GET /v1/convai/conversations/{conversation_id}
        
        Args:
            conversation_id: Unique conversation identifier
            
        Returns:
            Conversation details including:
            - conversation_id: Unique ID
            - agent_id: Agent that handled the call
            - status: Conversation status (completed, in_progress, etc.)
            - transcript: List of transcript entries with role and message
            - metadata: Call metadata (duration, timestamps, etc.)
            
        Example:
            >>> conv = service.get_conversation("conv_abc123")
            >>> for entry in conv.get("transcript", []):
            ...     print(f"{entry['role']}: {entry['message']}")
        """
        with APICallLogger(self.logger, "Get Conversation", conversation_id=conversation_id):
            response = self._make_request(
                method="GET",
                endpoint=f"{self.CONVERSATIONS_ENDPOINT}/{conversation_id}"
            )
            
            self.logger.info(f"Retrieved conversation: {conversation_id}")
            return response
    
    def get_conversation_audio(self, conversation_id: str) -> bytes:
        """
        Get the audio recording of a conversation.
        
        API Endpoint: GET /v1/convai/conversations/{conversation_id}/audio
        
        Args:
            conversation_id: Unique conversation identifier
            
        Returns:
            Audio file content as bytes (MP3 format)
            
        Note:
            This returns raw bytes, not JSON. Save to file or stream as needed.
            
        Example:
            >>> audio = service.get_conversation_audio("conv_abc123")
            >>> with open("recording.mp3", "wb") as f:
            ...     f.write(audio)
        """
        with APICallLogger(self.logger, "Get Conversation Audio", conversation_id=conversation_id):
            url = f"{self.config.base_url}{self.CONVERSATIONS_ENDPOINT}/{conversation_id}/audio"
            
            response = self.session.get(
                url,
                headers=self.config.headers,
                timeout=self.config.timeout
            )
            
            if not response.ok:
                from exceptions import raise_for_status
                try:
                    response_data = response.json()
                except ValueError:
                    response_data = {"error": response.text}
                raise_for_status(response.status_code, response_data)
            
            self.logger.info(f"Retrieved audio for conversation: {conversation_id}")
            return response.content
    
    def list_conversations(
        self,
        agent_id: Optional[str] = None,
        cursor: Optional[str] = None,
        page_size: int = 30
    ) -> Dict[str, Any]:
        """
        List conversations with optional filtering.
        
        API Endpoint: GET /v1/convai/conversations
        
        Args:
            agent_id: Filter by agent ID (optional)
            cursor: Pagination cursor for next page
            page_size: Number of results per page (default: 30)
            
        Returns:
            List of conversations with pagination info
            
        Example:
            >>> result = service.list_conversations(agent_id="agent_abc123")
            >>> for conv in result.get("conversations", []):
            ...     print(f"{conv['conversation_id']}: {conv['status']}")
        """
        with APICallLogger(self.logger, "List Conversations"):
            params = {"page_size": page_size}
            if agent_id:
                params["agent_id"] = agent_id
            if cursor:
                params["cursor"] = cursor
            
            response = self._make_request(
                method="GET",
                endpoint=self.CONVERSATIONS_ENDPOINT,
                params=params
            )
            
            count = len(response.get("conversations", []))
            self.logger.info(f"Retrieved {count} conversations")
            return response
    
    def delete_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """
        Delete a conversation.
        
        API Endpoint: DELETE /v1/convai/conversations/{conversation_id}
        
        Args:
            conversation_id: Conversation ID to delete
            
        Returns:
            Deletion confirmation
        """
        with APICallLogger(self.logger, "Delete Conversation", conversation_id=conversation_id):
            response = self._make_request(
                method="DELETE",
                endpoint=f"{self.CONVERSATIONS_ENDPOINT}/{conversation_id}"
            )
            
            self.logger.info(f"Deleted conversation: {conversation_id}")
            return response
