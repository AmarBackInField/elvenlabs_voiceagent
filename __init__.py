"""
ElevenLabs Agent Client Package.

A comprehensive Python client for interacting with ElevenLabs Conversational AI API.

Features:
- Agent management (create, get, update, delete)
- Phone number import and management
- SIP trunk configuration and outbound calls
- Batch calling job submission and management

Architecture:
- Modular service classes for each API domain
- Unified client facade for easy access
- Comprehensive logging and error handling

Usage:
    # Using unified client (recommended)
    from elevenlabs_agent import ElevenLabsClient
    
    client = ElevenLabsClient()
    agent = client.agents.create_agent(
        name="My Agent",
        voice_id="voice_id",
        first_message="Hello!"
    )
    
    # Using individual services
    from elevenlabs_agent import AgentService, ElevenLabsConfig
    
    config = ElevenLabsConfig.from_env()
    agent_service = AgentService(config)
    agent = agent_service.create_agent(...)
"""

# Main unified client
from client import ElevenLabsClient

# Individual service classes
from agents import AgentService
from phone_numbers import PhoneNumberService
from sip_trunk import SIPTrunkService
from batch_calling import BatchCallingService

# Base client for custom services
from base import BaseClient

# Configuration
from config import ElevenLabsConfig

# Exceptions
from exceptions import (
    ElevenLabsError,
    AuthenticationError,
    RateLimitError,
    NotFoundError,
    ValidationError,
    ServerError,
    ConnectionError,
    TimeoutError,
    AgentError,
    SIPTrunkError,
    BatchCallError
)

# Logging utilities
from logger import setup_logger, log_api_call, APICallLogger

__version__ = "1.0.0"
__author__ = "ElevenLabs Agent Client"

__all__ = [
    # Main unified client
    "ElevenLabsClient",
    
    # Individual service classes
    "AgentService",
    "PhoneNumberService",
    "SIPTrunkService",
    "BatchCallingService",
    
    # Base client
    "BaseClient",
    
    # Configuration
    "ElevenLabsConfig",
    
    # Exceptions
    "ElevenLabsError",
    "AuthenticationError",
    "RateLimitError",
    "NotFoundError",
    "ValidationError",
    "ServerError",
    "ConnectionError",
    "TimeoutError",
    "AgentError",
    "SIPTrunkError",
    "BatchCallError",
    
    # Logging utilities
    "setup_logger",
    "log_api_call",
    "APICallLogger",
]
