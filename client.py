"""
ElevenLabs API Client.
Main facade that provides unified access to all ElevenLabs services.
"""

from typing import Optional

from config import ElevenLabsConfig
from logger import setup_logger
from agents import AgentService
from phone_numbers import PhoneNumberService
from sip_trunk import SIPTrunkService
from batch_calling import BatchCallingService
from conversations import ConversationService
from knowledge_base import KnowledgeBaseService
from tools import ToolsService


class ElevenLabsClient:
    """
    Unified ElevenLabs API Client.
    
    Provides access to all ElevenLabs services through a single interface.
    Each service is accessible as an attribute:
    
    - agents: Agent management (create, get, delete)
    - phone_numbers: Phone number import and management
    - sip_trunk: SIP trunk configuration and outbound calls
    - batch_calling: Batch calling job submission
    - conversations: Conversation history, transcripts, and recordings
    - knowledge_base: Document ingestion from text, URL, or file
    - tools: Custom tools for agent function calls
    
    Example:
        >>> client = ElevenLabsClient()
        >>> 
        >>> # Create an agent
        >>> agent = client.agents.create_agent(
        ...     name="My Agent",
        ...     voice_id="21m00Tcm4TlvDq8ikWAM",
        ...     first_message="Hello!"
        ... )
        >>> 
        >>> # Make an outbound call
        >>> call = client.sip_trunk.outbound_call(
        ...     agent_id=agent["agent_id"],
        ...     agent_phone_number_id="ph_123",
        ...     to_number="+14155551234"
        ... )
        >>> 
        >>> # Submit batch calling job
        >>> job = client.batch_calling.submit_job(
        ...     call_name="Campaign",
        ...     agent_id=agent["agent_id"],
        ...     recipients=[{"phone_number": "+14155551234"}]
        ... )
    
    Attributes:
        config: Configuration instance
        agents: AgentService for agent management
        phone_numbers: PhoneNumberService for phone number operations
        sip_trunk: SIPTrunkService for SIP and outbound calls
        batch_calling: BatchCallingService for batch operations
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        config: Optional[ElevenLabsConfig] = None,
        log_level: str = "INFO",
        log_file: Optional[str] = None
    ):
        """
        Initialize ElevenLabs client with all services.
        
        Args:
            api_key: ElevenLabs API key (overrides environment variable)
            base_url: API base URL (overrides environment variable)
            config: Optional pre-configured ElevenLabsConfig instance
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Optional log file path for file-based logging
        """
        # Initialize configuration
        if config:
            self.config = config
        else:
            self.config = ElevenLabsConfig.from_env(api_key=api_key, base_url=base_url)
        
        # Override log level if provided
        self.config.log_level = log_level
        
        # Initialize main logger
        self.logger = setup_logger(
            name="elevenlabs.client",
            level=log_level,
            log_file=log_file
        )
        
        # Initialize services
        self.agents = AgentService(self.config)
        self.phone_numbers = PhoneNumberService(self.config)
        self.sip_trunk = SIPTrunkService(self.config)
        self.batch_calling = BatchCallingService(self.config)
        self.conversations = ConversationService(self.config)
        self.knowledge_base = KnowledgeBaseService(self.config)
        self.tools = ToolsService(self.config)
        
        self.logger.info(f"ElevenLabsClient initialized with base URL: {self.config.base_url}")
    
    def health_check(self) -> bool:
        """
        Check if the API is accessible.
        
        Returns:
            True if API is accessible, False otherwise
        """
        try:
            self.agents.list_agents(page_size=1)
            self.logger.info("API health check passed")
            return True
        except Exception as e:
            self.logger.error(f"API health check failed: {str(e)}")
            return False
    
    def close(self):
        """Close all service sessions."""
        self.agents.close()
        self.phone_numbers.close()
        self.sip_trunk.close()
        self.batch_calling.close()
        self.conversations.close()
        self.knowledge_base.close()
        self.tools.close()
        self.logger.info("All client sessions closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False
    
    # =========================================================================
    # Convenience Methods (Delegate to services)
    # =========================================================================
    
    def create_agent(self, **kwargs):
        """
        Convenience method: Create an agent.
        Delegates to agents.create_agent()
        """
        return self.agents.create_agent(**kwargs)
    
    def get_agent(self, agent_id: str):
        """
        Convenience method: Get agent details.
        Delegates to agents.get_agent()
        """
        return self.agents.get_agent(agent_id)
    
    def delete_agent(self, agent_id: str):
        """
        Convenience method: Delete an agent.
        Delegates to agents.delete_agent()
        """
        return self.agents.delete_agent(agent_id)
    
    def outbound_call(self, **kwargs):
        """
        Convenience method: Make outbound call via SIP.
        Delegates to sip_trunk.outbound_call()
        """
        return self.sip_trunk.outbound_call(**kwargs)
    
    def submit_batch_job(self, **kwargs):
        """
        Convenience method: Submit batch calling job.
        Delegates to batch_calling.submit_job()
        """
        return self.batch_calling.submit_job(**kwargs)


# Singleton instance for convenience
_client_instance: Optional[ElevenLabsClient] = None


def get_elevenlabs_client() -> ElevenLabsClient:
    """
    Get a singleton instance of ElevenLabsClient.
    
    Creates the client on first call and reuses it for subsequent calls.
    Useful for background tasks and automation endpoints.
    """
    global _client_instance
    if _client_instance is None:
        _client_instance = ElevenLabsClient()
    return _client_instance
