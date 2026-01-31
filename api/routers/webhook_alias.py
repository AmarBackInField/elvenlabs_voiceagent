"""
Webhook Alias Router.
Provides /webhook/ (singular) as an alias for /webhooks/ (plural) for backward compatibility.
"""

from fastapi import APIRouter, Request
from api.routers.webhooks import (
    webhook_get_products,
    webhook_get_orders,
    webhook_test,
    email_webhook,
    WebhookResponse
)

router = APIRouter(
    prefix="/webhook",
    tags=["Webhooks (Alias)"]
)


@router.post(
    "/ecommerce/products",
    response_model=WebhookResponse,
    summary="Get Products (Alias)",
    description="Alias for /webhooks/ecommerce/products"
)
async def alias_get_products(request: Request):
    """Alias route for backward compatibility."""
    return await webhook_get_products(request)


@router.post(
    "/ecommerce/orders",
    response_model=WebhookResponse,
    summary="Get Orders (Alias)",
    description="Alias for /webhooks/ecommerce/orders"
)
async def alias_get_orders(request: Request):
    """Alias route for backward compatibility."""
    return await webhook_get_orders(request)


@router.post(
    "/test",
    response_model=WebhookResponse,
    summary="Test Webhook (Alias)",
    description="Alias for /webhooks/test"
)
async def alias_test(request: Request):
    """Alias route for backward compatibility."""
    return await webhook_test(request)


@router.post(
    "/email/{template_id}",
    response_model=WebhookResponse,
    summary="Email Webhook (Alias)",
    description="Alias for /webhooks/email/{template_id}"
)
async def alias_email(template_id: str, request: Request):
    """Alias route for backward compatibility."""
    return await email_webhook(template_id, request)
