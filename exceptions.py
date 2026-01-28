"""
Custom exceptions for ElevenLabs API Client.
Provides specific exception types for different error scenarios.
"""


class ElevenLabsError(Exception):
    """Base exception for all ElevenLabs API errors."""
    
    def __init__(self, message: str, status_code: int = None, response: dict = None):
        """
        Initialize ElevenLabs error.
        
        Args:
            message: Error message
            status_code: HTTP status code (if applicable)
            response: Raw API response (if available)
        """
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.message)
    
    def __str__(self):
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class AuthenticationError(ElevenLabsError):
    """Raised when API authentication fails."""
    pass


class RateLimitError(ElevenLabsError):
    """Raised when API rate limit is exceeded."""
    
    def __init__(self, message: str, retry_after: int = None, **kwargs):
        """
        Initialize rate limit error.
        
        Args:
            message: Error message
            retry_after: Seconds to wait before retrying
            **kwargs: Additional arguments passed to parent
        """
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class NotFoundError(ElevenLabsError):
    """Raised when a requested resource is not found."""
    pass


class ValidationError(ElevenLabsError):
    """Raised when request validation fails."""
    pass


class ServerError(ElevenLabsError):
    """Raised when the server returns an error."""
    pass


class ConnectionError(ElevenLabsError):
    """Raised when connection to API fails."""
    pass


class TimeoutError(ElevenLabsError):
    """Raised when API request times out."""
    pass


class AgentError(ElevenLabsError):
    """Raised for agent-specific errors."""
    pass


class SIPTrunkError(ElevenLabsError):
    """Raised for SIP trunk related errors."""
    pass


class BatchCallError(ElevenLabsError):
    """Raised for batch calling errors."""
    pass


def raise_for_status(status_code: int, response = None):
    """
    Raise appropriate exception based on HTTP status code.
    
    Args:
        status_code: HTTP status code
        response: API response body (dict or string)
        
    Raises:
        Appropriate ElevenLabsError subclass
    """
    message = "Unknown error"
    
    if response:
        if isinstance(response, dict):
            # Try to extract message from various possible response structures
            detail = response.get("detail", {})
            if isinstance(detail, dict):
                message = detail.get("message", response.get("message", 
                          response.get("error", str(response))))
            else:
                # detail is a string
                message = str(detail)
        else:
            # response is a string or other type
            message = str(response)
    
    if status_code == 401:
        raise AuthenticationError(
            message=message or "Invalid API key or unauthorized access",
            status_code=status_code,
            response=response
        )
    
    elif status_code == 403:
        raise AuthenticationError(
            message=message or "Access forbidden",
            status_code=status_code,
            response=response
        )
    
    elif status_code == 404:
        raise NotFoundError(
            message=message or "Resource not found",
            status_code=status_code,
            response=response
        )
    
    elif status_code == 422:
        raise ValidationError(
            message=message or "Validation error",
            status_code=status_code,
            response=response
        )
    
    elif status_code == 429:
        retry_after = None
        if response and isinstance(response, dict):
            retry_after = response.get("retry_after")
        raise RateLimitError(
            message=message or "Rate limit exceeded",
            status_code=status_code,
            response=response,
            retry_after=retry_after
        )
    
    elif 500 <= status_code < 600:
        raise ServerError(
            message=message or "Server error",
            status_code=status_code,
            response=response
        )
    
    elif status_code >= 400:
        raise ElevenLabsError(
            message=message,
            status_code=status_code,
            response=response
        )
