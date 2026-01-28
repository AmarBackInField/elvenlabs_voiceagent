"""
Ecommerce Router.
Handles product and order lookups during calls.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from api.schemas import (
    EcommerceCredentials,
    EcommerceProductsResponse,
    EcommerceOrdersResponse,
    SuccessResponse,
    ErrorResponse
)
from ecommerce import get_ecommerce_service, EcommerceClient


router = APIRouter(
    prefix="/ecommerce",
    tags=["Ecommerce"],
    responses={
        401: {"model": ErrorResponse, "description": "Authentication failed"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)


@router.get(
    "/products/{conversation_id}",
    response_model=EcommerceProductsResponse,
    summary="Get Products for Conversation",
    description="Fetch products for an active conversation with ecommerce enabled"
)
async def get_products_for_conversation(
    conversation_id: str,
    limit: int = Query(5, ge=1, le=20, description="Number of products to fetch")
):
    """
    Fetch products for an active conversation.
    
    The conversation must have been initiated with ecommerce_credentials.
    """
    ecommerce_service = get_ecommerce_service()
    result = ecommerce_service.get_products(session_id=conversation_id, limit=limit)
    
    return EcommerceProductsResponse(
        success=result.get("success", False),
        products=result.get("products", []),
        formatted=result.get("formatted"),
        count=result.get("count", 0),
        error=result.get("error")
    )


@router.get(
    "/orders/{conversation_id}",
    response_model=EcommerceOrdersResponse,
    summary="Get Orders for Conversation",
    description="Fetch orders for an active conversation with ecommerce enabled"
)
async def get_orders_for_conversation(
    conversation_id: str,
    limit: int = Query(5, ge=1, le=20, description="Number of orders to fetch")
):
    """
    Fetch orders for an active conversation.
    
    The conversation must have been initiated with ecommerce_credentials.
    """
    ecommerce_service = get_ecommerce_service()
    result = ecommerce_service.get_orders(session_id=conversation_id, limit=limit)
    
    return EcommerceOrdersResponse(
        success=result.get("success", False),
        orders=result.get("orders", []),
        formatted=result.get("formatted"),
        count=result.get("count", 0),
        error=result.get("error")
    )


@router.post(
    "/connect/{conversation_id}",
    response_model=SuccessResponse,
    summary="Connect Ecommerce to Conversation",
    description="Connect ecommerce platform to an existing conversation"
)
async def connect_ecommerce(
    conversation_id: str,
    credentials: EcommerceCredentials
):
    """
    Connect an ecommerce platform to an existing conversation.
    
    Use this if you need to enable ecommerce for a conversation that was
    started without ecommerce_credentials.
    """
    try:
        ecommerce_service = get_ecommerce_service()
        ecommerce_service.create_client(
            session_id=conversation_id,
            platform=credentials.platform,
            base_url=credentials.base_url,
            api_key=credentials.api_key,
            api_secret=credentials.api_secret,
            access_token=credentials.access_token
        )
        
        return SuccessResponse(
            message=f"Ecommerce ({credentials.platform}) connected to conversation {conversation_id}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/disconnect/{conversation_id}",
    response_model=SuccessResponse,
    summary="Disconnect Ecommerce from Conversation",
    description="Disconnect ecommerce platform from a conversation"
)
async def disconnect_ecommerce(conversation_id: str):
    """
    Disconnect ecommerce platform from a conversation.
    
    Call this when a conversation ends to clean up resources.
    """
    ecommerce_service = get_ecommerce_service()
    ecommerce_service.remove_client(conversation_id)
    
    return SuccessResponse(message=f"Ecommerce disconnected from conversation {conversation_id}")


@router.post(
    "/test",
    response_model=EcommerceProductsResponse,
    summary="Test Ecommerce Connection",
    description="Test ecommerce credentials by fetching products"
)
async def test_ecommerce_connection(credentials: EcommerceCredentials):
    """
    Test ecommerce credentials without starting a conversation.
    
    Useful for validating API keys and configuration.
    """
    try:
        client = EcommerceClient(
            platform=credentials.platform,
            base_url=credentials.base_url,
            api_key=credentials.api_key,
            api_secret=credentials.api_secret,
            access_token=credentials.access_token
        )
        
        result = client.get_products(limit=3)
        
        return EcommerceProductsResponse(
            success=result.get("success", False),
            products=result.get("products", []),
            formatted=result.get("formatted"),
            count=result.get("count", 0),
            error=result.get("error")
        )
        
    except Exception as e:
        return EcommerceProductsResponse(
            success=False,
            products=[],
            error=str(e)
        )
