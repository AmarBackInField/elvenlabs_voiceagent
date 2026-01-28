"""
Logging configuration for ElevenLabs API Client.
Provides structured logging with customizable formatters and handlers.
"""

import logging
import sys
from typing import Optional
from functools import wraps
from time import time


def setup_logger(
    name: str = "elevenlabs",
    level: str = "INFO",
    log_format: Optional[str] = None,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Set up and configure a logger instance.
    
    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Custom log format string
        log_file: Optional file path for file logging
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Set log level
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # Default format
    if log_format is None:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
    
    formatter = logging.Formatter(log_format)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


def log_api_call(logger: logging.Logger):
    """
    Decorator for logging API calls with timing information.
    
    Args:
        logger: Logger instance to use for logging
        
    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract method name and relevant info
            method_name = func.__name__
            
            # Log request start
            logger.info(f"API Call Started: {method_name}")
            logger.debug(f"Arguments: args={args[1:]}, kwargs={kwargs}")
            
            start_time = time()
            
            try:
                result = func(*args, **kwargs)
                
                # Calculate duration
                duration = time() - start_time
                
                # Log success
                logger.info(f"API Call Completed: {method_name} (Duration: {duration:.3f}s)")
                logger.debug(f"Response: {result}")
                
                return result
                
            except Exception as e:
                # Calculate duration
                duration = time() - start_time
                
                # Log failure
                logger.error(f"API Call Failed: {method_name} (Duration: {duration:.3f}s) - Error: {str(e)}")
                raise
                
        return wrapper
    return decorator


class APICallLogger:
    """Context manager for logging API calls."""
    
    def __init__(self, logger: logging.Logger, operation: str, **context):
        """
        Initialize API call logger.
        
        Args:
            logger: Logger instance
            operation: Name of the operation being performed
            **context: Additional context to log
        """
        self.logger = logger
        self.operation = operation
        self.context = context
        self.start_time = None
    
    def __enter__(self):
        """Log operation start."""
        self.start_time = time()
        self.logger.info(f"Starting: {self.operation}")
        if self.context:
            self.logger.debug(f"Context: {self.context}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Log operation end."""
        duration = time() - self.start_time
        
        if exc_type is None:
            self.logger.info(f"Completed: {self.operation} (Duration: {duration:.3f}s)")
        else:
            self.logger.error(
                f"Failed: {self.operation} (Duration: {duration:.3f}s) - "
                f"Error: {exc_type.__name__}: {exc_val}"
            )
        
        # Don't suppress exceptions
        return False
