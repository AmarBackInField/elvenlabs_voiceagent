"""
FastAPI Application for ElevenLabs Agent API.
Main entry point with all routers included.
"""

import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.routers.agents import router as agents_router
from api.routers.phone_numbers import router as phone_numbers_router
from api.routers.sip_trunk import router as sip_trunk_router
from api.routers.batch_calling import router as batch_calling_router
from api.routers.conversations import router as conversations_router
from api.routers.knowledge_base import router as knowledge_base_router
from api.routers.ecommerce import router as ecommerce_router
from api.routers.tools import router as tools_router
from api.routers.webhooks import router as webhooks_router
from api.dependencies import ClientManager, get_config
from api.schemas import HealthResponse, ErrorResponse
from logger import setup_logger
from exceptions import ElevenLabsError, AuthenticationError


# Setup logger
logger = setup_logger(name="elevenlabs.api", level="INFO")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting ElevenLabs API server...")
    
    try:
        # Validate configuration on startup
        config = get_config()
        logger.info(f"Configuration loaded. Base URL: {config.base_url}")
    except Exception as e:
        logger.error(f"Configuration error: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down ElevenLabs API server...")
    ClientManager.close()
    logger.info("Cleanup complete")


# Create FastAPI application
app = FastAPI(
    title="ElevenLabs Agent API",
    description="""
## ElevenLabs Conversational AI API Wrapper

A FastAPI wrapper for ElevenLabs Conversational AI platform.

### Features

- **Agent Management**: Create, update, delete, and list AI agents
- **Phone Numbers**: Import and manage phone numbers from Twilio/SIP providers
- **SIP Trunk**: Make outbound calls via SIP trunk
- **Batch Calling**: Submit and manage batch calling campaigns

### Authentication

All endpoints require an ElevenLabs API key configured via environment variable:
```
ELEVENLABS_API_KEY=your_api_key_here
```

### Rate Limits

Respects ElevenLabs API rate limits. 429 errors include retry-after information.
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)


# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(ElevenLabsError)
async def elevenlabs_exception_handler(request: Request, exc: ElevenLabsError):
    """Handle ElevenLabs API errors."""
    logger.error(f"ElevenLabs error: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code or 500,
        content={
            "success": False,
            "error": exc.message,
            "detail": str(exc.response) if exc.response else None
        }
    )


@app.exception_handler(AuthenticationError)
async def auth_exception_handler(request: Request, exc: AuthenticationError):
    """Handle authentication errors."""
    logger.error(f"Authentication error: {exc.message}")
    return JSONResponse(
        status_code=401,
        content={
            "success": False,
            "error": "Authentication failed",
            "detail": exc.message
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors."""
    logger.exception(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc) if app.debug else None
        }
    )


# =============================================================================
# Include Routers
# =============================================================================

# Agents router - /api/v1/agents
app.include_router(
    agents_router,
    prefix="/api/v1",
    tags=["Agents"]
)

# Phone Numbers router - /api/v1/phone-numbers
app.include_router(
    phone_numbers_router,
    prefix="/api/v1",
    tags=["Phone Numbers"]
)

# SIP Trunk router - /api/v1/sip-trunk
app.include_router(
    sip_trunk_router,
    prefix="/api/v1",
    tags=["SIP Trunk"]
)

# Batch Calling router - /api/v1/batch-calling
app.include_router(
    batch_calling_router,
    prefix="/api/v1",
    tags=["Batch Calling"]
)

# Conversations router - /api/v1/conversations
app.include_router(
    conversations_router,
    prefix="/api/v1",
    tags=["Conversations"]
)

# Knowledge Base router - /api/v1/knowledge-base
app.include_router(
    knowledge_base_router,
    prefix="/api/v1",
    tags=["Knowledge Base"]
)

# Ecommerce router - /api/v1/ecommerce
app.include_router(
    ecommerce_router,
    prefix="/api/v1",
    tags=["Ecommerce"]
)

# Tools router - /api/v1/tools
app.include_router(
    tools_router,
    prefix="/api/v1",
    tags=["Tools"]
)

# Webhooks router - /api/v1/webhooks (called by ElevenLabs agents)
app.include_router(
    webhooks_router,
    prefix="/api/v1",
    tags=["Webhooks"]
)

# Webhook alias router - /api/v1/webhook (singular, for backward compatibility)
from api.routers.webhook_alias import router as webhook_alias_router
app.include_router(
    webhook_alias_router,
    prefix="/api/v1",
    tags=["Webhooks"]
)

# Email Templates router - /api/v1/email-templates
from api.routers.email_templates import router as email_templates_router
app.include_router(
    email_templates_router,
    prefix="/api/v1",
    tags=["Email Templates"]
)


# =============================================================================
# Root Endpoints
# =============================================================================

@app.get(
    "/",
    tags=["Root"],
    summary="API Root",
    description="Welcome endpoint with API information"
)
async def root():
    """API root endpoint."""
    return {
        "name": "ElevenLabs Agent API",
        "version": "1.0.0",
        "documentation": "/docs",
        "endpoints": {
            "agents": "/api/v1/agents",
            "phone_numbers": "/api/v1/phone-numbers",
            "sip_trunk": "/api/v1/sip-trunk",
            "batch_calling": "/api/v1/batch-calling"
        }
    }


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Health Check",
    description="Check API health and ElevenLabs connectivity"
)
async def health_check():
    """
    Health check endpoint.
    
    Verifies:
    - API is running
    - Configuration is valid
    - ElevenLabs API is accessible
    """
    try:
        # Quick config check
        config = get_config()
        
        # Try to create a client and check API
        from client import ElevenLabsClient
        with ElevenLabsClient(config=config) as client:
            api_accessible = client.health_check()
        
        return HealthResponse(
            status="healthy" if api_accessible else "degraded",
            api_accessible=api_accessible,
            version="1.0.0"
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            api_accessible=False,
            version="1.0.0"
        )


# =============================================================================
# Run with Uvicorn
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
