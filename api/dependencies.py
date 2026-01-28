"""
FastAPI dependencies for dependency injection.
"""

import os
from typing import Generator
from functools import lru_cache

from client import ElevenLabsClient
from config import ElevenLabsConfig
from logger import setup_logger


# Logger for dependencies
logger = setup_logger(name="elevenlabs.api.deps", level="INFO")


@lru_cache()
def get_config() -> ElevenLabsConfig:
    """
    Get cached configuration instance.
    Configuration is loaded once and cached.
    
    Returns:
        ElevenLabsConfig instance
    """
    try:
        config = ElevenLabsConfig.from_env()
        logger.info("Configuration loaded successfully")
        return config
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise


def get_client() -> Generator[ElevenLabsClient, None, None]:
    """
    Dependency that provides ElevenLabs client.
    Creates a new client per request and closes it after.
    
    Yields:
        ElevenLabsClient instance
    """
    client = None
    try:
        config = get_config()
        client = ElevenLabsClient(config=config)
        yield client
    finally:
        if client:
            client.close()


class ClientManager:
    """
    Singleton client manager for persistent client connection.
    Use this for better performance in high-load scenarios.
    """
    
    _instance: ElevenLabsClient = None
    
    @classmethod
    def get_client(cls) -> ElevenLabsClient:
        """Get or create singleton client instance."""
        if cls._instance is None:
            config = get_config()
            cls._instance = ElevenLabsClient(config=config)
            logger.info("Singleton client created")
        return cls._instance
    
    @classmethod
    def close(cls):
        """Close the singleton client."""
        if cls._instance:
            cls._instance.close()
            cls._instance = None
            logger.info("Singleton client closed")


def get_persistent_client() -> ElevenLabsClient:
    """
    Dependency that provides persistent ElevenLabs client.
    Uses singleton pattern - better for high-load scenarios.
    
    Returns:
        ElevenLabsClient instance
    """
    return ClientManager.get_client()
