"""
Base HTTP client for ElevenLabs API.
Provides common HTTP functionality for all service classes.
"""

from typing import Optional, Dict, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import ElevenLabsConfig
from logger import setup_logger
from exceptions import (
    ElevenLabsError,
    ConnectionError,
    TimeoutError,
    raise_for_status
)


class BaseClient:
    """
    Base HTTP client with common functionality.
    
    Provides:
    - HTTP session management with retry logic
    - Request/response handling
    - Error handling and logging
    
    All service classes inherit from this base.
    """
    
    def __init__(
        self,
        config: ElevenLabsConfig,
        logger_name: str = "elevenlabs.base"
    ):
        """
        Initialize base client.
        
        Args:
            config: ElevenLabsConfig instance
            logger_name: Name for the logger
        """
        self.config = config
        self.logger = setup_logger(name=logger_name, level=config.log_level)
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """
        Create a requests session with retry logic.
        
        Returns:
            Configured requests session
        """
        session = requests.Session()
        
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=self.config.retry_delay,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to the API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE, PATCH)
            endpoint: API endpoint path
            data: Request body data
            params: Query parameters
            headers: Additional headers
            
        Returns:
            API response as dictionary
            
        Raises:
            ElevenLabsError: On API errors
            ConnectionError: On connection failures
            TimeoutError: On request timeout
        """
        url = f"{self.config.base_url}{endpoint}"
        
        request_headers = self.config.headers.copy()
        if headers:
            request_headers.update(headers)
        
        self.logger.debug(f"Making {method} request to {url}")
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=request_headers,
                timeout=self.config.timeout
            )
            
            self.logger.debug(f"Response status: {response.status_code}")
            
            try:
                response_data = response.json() if response.content else {}
            except ValueError:
                response_data = {"raw_content": response.text}
            
            if not response.ok:
                raise_for_status(response.status_code, response_data)
            
            return response_data
            
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Connection error: {str(e)}")
            raise ConnectionError(f"Failed to connect to API: {str(e)}")
            
        except requests.exceptions.Timeout as e:
            self.logger.error(f"Request timeout: {str(e)}")
            raise TimeoutError(f"Request timed out: {str(e)}")
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request error: {str(e)}")
            raise ElevenLabsError(f"Request failed: {str(e)}")
    
    def close(self):
        """Close the HTTP session."""
        self.session.close()
        self.logger.info("Session closed")
