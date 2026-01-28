"""
API Routers for ElevenLabs endpoints.
"""

from api.routers.agents import router as agents_router
from api.routers.phone_numbers import router as phone_numbers_router
from api.routers.sip_trunk import router as sip_trunk_router
from api.routers.batch_calling import router as batch_calling_router
from api.routers.conversations import router as conversations_router
from api.routers.knowledge_base import router as knowledge_base_router
from api.routers.ecommerce import router as ecommerce_router
from api.routers.tools import router as tools_router
from api.routers.webhooks import router as webhooks_router
from api.routers.email_templates import router as email_templates_router

__all__ = [
    "agents_router",
    "phone_numbers_router", 
    "sip_trunk_router",
    "batch_calling_router",
    "conversations_router",
    "knowledge_base_router",
    "ecommerce_router",
    "tools_router",
    "webhooks_router",
    "email_templates_router"
]
