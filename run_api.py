#!/usr/bin/env python3
"""
Run script for ElevenLabs Agent API.
Starts the FastAPI server with configurable options.
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

import uvicorn
from dotenv import load_dotenv


def main():
    """Run the FastAPI server."""
    
    # Load environment variables
    load_dotenv()
    
    # Server configuration from environment
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    reload = os.getenv("API_RELOAD", "true").lower() == "true"
    log_level = os.getenv("API_LOG_LEVEL", "info").lower()
    workers = int(os.getenv("API_WORKERS", "1"))
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║           ElevenLabs Agent API Server                        ║
╠══════════════════════════════════════════════════════════════╣
║  Host: {host:<54} ║
║  Port: {port:<54} ║
║  Reload: {str(reload):<52} ║
║  Log Level: {log_level:<49} ║
║  Workers: {workers:<51} ║
╠══════════════════════════════════════════════════════════════╣
║  Documentation: http://{host}:{port}/docs{' ' * (38 - len(str(port)))}║
║  OpenAPI JSON:  http://{host}:{port}/openapi.json{' ' * (30 - len(str(port)))}║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Run the server
    if reload:
        # Development mode with auto-reload
        uvicorn.run(
            "api.main:app",
            host=host,
            port=port,
            reload=reload,
            log_level=log_level
        )
    else:
        # Production mode with multiple workers
        uvicorn.run(
            "api.main:app",
            host=host,
            port=port,
            workers=workers,
            log_level=log_level
        )


if __name__ == "__main__":
    main()
