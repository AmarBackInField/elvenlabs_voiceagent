"""
Configuration management for ElevenLabs API Client.
Handles environment variables and default settings.
"""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ElevenLabsConfig:
    """Configuration class for ElevenLabs API settings."""
    
    # API Configuration
    api_key: str = field(default_factory=lambda: os.getenv("ELEVENLABS_API_KEY", ""))
    base_url: str = field(default_factory=lambda: os.getenv("ELEVENLABS_BASE_URL", "https://api.elevenlabs.io"))
    
    # Request Configuration
    timeout: int = field(default_factory=lambda: int(os.getenv("ELEVENLABS_TIMEOUT", "30")))
    max_retries: int = field(default_factory=lambda: int(os.getenv("ELEVENLABS_MAX_RETRIES", "3")))
    retry_delay: float = field(default_factory=lambda: float(os.getenv("ELEVENLABS_RETRY_DELAY", "1.0")))
    
    # Logging Configuration
    log_level: str = field(default_factory=lambda: os.getenv("ELEVENLABS_LOG_LEVEL", "INFO"))
    log_format: str = field(default_factory=lambda: os.getenv(
        "ELEVENLABS_LOG_FORMAT",
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    ))
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.api_key:
            raise ValueError("ELEVENLABS_API_KEY environment variable is required")
        
        if not self.base_url:
            raise ValueError("Base URL cannot be empty")
        
        # Remove trailing slash from base_url if present
        self.base_url = self.base_url.rstrip("/")
    
    @property
    def headers(self) -> dict:
        """Return default headers for API requests."""
        return {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    @classmethod
    def from_env(cls, api_key: Optional[str] = None, base_url: Optional[str] = None) -> "ElevenLabsConfig":
        """
        Create configuration from environment variables with optional overrides.
        
        Args:
            api_key: Optional API key override
            base_url: Optional base URL override
            
        Returns:
            ElevenLabsConfig instance
        """
        config_kwargs = {}
        
        if api_key:
            config_kwargs["api_key"] = api_key
        if base_url:
            config_kwargs["base_url"] = base_url
            
        return cls(**config_kwargs)
