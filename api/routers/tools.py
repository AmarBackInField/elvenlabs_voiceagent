"""
Tools Router.
Manages custom tools for ElevenLabs agents.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from client import ElevenLabsClient
from api.dependencies import get_client
from api.schemas import SuccessResponse, ErrorResponse
from exceptions import ElevenLabsError, NotFoundError


router = APIRouter(
    prefix="/tools",
    tags=["Tools"],
    responses={
        401: {"model": ErrorResponse, "description": "Authentication failed"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)


class ToolParameter(BaseModel):
    """Tool parameter definition."""
    name: str = Field(..., description="Parameter name")
    type: str = Field("string", description="Parameter type (string, integer, boolean)")
    description: str = Field("", description="Parameter description")
    required: bool = Field(False, description="Whether parameter is required")


class CreateWebhookToolRequest(BaseModel):
    """Request to create a webhook tool."""
    name: str = Field(..., description="Tool name (used in function calls)")
    description: str = Field(..., description="What the tool does (helps LLM understand when to use it)")
    webhook_url: str = Field(..., description="URL to call when tool is invoked")
    http_method: str = Field("POST", description="HTTP method")
    parameters: Optional[List[ToolParameter]] = Field(None, description="Tool parameters")
    headers: Optional[Dict[str, str]] = Field(None, description="Additional headers")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "get_products",
                "description": "Fetch products from the store. Use when user asks about products or inventory.",
                "webhook_url": "https://your-api.com/api/v1/webhook/ecommerce/products",
                "parameters": [
                    {"name": "limit", "type": "integer", "description": "Number of products", "required": False}
                ]
            }
        }


class CreateEcommerceToolsRequest(BaseModel):
    """Request to create ecommerce tools."""
    webhook_base_url: str = Field(..., description="Base URL for webhook endpoints")
    
    class Config:
        json_schema_extra = {
            "example": {
                "webhook_base_url": "https://your-api.com/api/v1"
            }
        }


class ToolResponse(BaseModel):
    """Tool details response."""
    tool_id: str
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    
    class Config:
        extra = "allow"


class ToolListResponse(BaseModel):
    """List of tools response."""
    tools: List[Dict[str, Any]]
    cursor: Optional[str] = None


class EcommerceToolsResponse(BaseModel):
    """Response with created ecommerce tool IDs."""
    products_tool_id: Optional[str] = None
    orders_tool_id: Optional[str] = None


@router.post(
    "/webhook",
    response_model=ToolResponse,
    status_code=201,
    summary="Create Webhook Tool",
    description="Create a tool that makes HTTP requests during conversations"
)
async def create_webhook_tool(
    request: CreateWebhookToolRequest,
    client: ElevenLabsClient = Depends(get_client)
):
    """
    Create a webhook tool for agents.
    
    Webhook tools allow agents to make HTTP requests to external APIs
    during conversations to fetch data or perform actions.
    """
    try:
        parameters = None
        if request.parameters:
            parameters = [p.model_dump() for p in request.parameters]
        
        result = client.tools.create_webhook_tool(
            name=request.name,
            description=request.description,
            webhook_url=request.webhook_url,
            http_method=request.http_method,
            parameters=parameters,
            headers=request.headers
        )
        return ToolResponse(**result)
        
    except ElevenLabsError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@router.post(
    "/ecommerce",
    response_model=EcommerceToolsResponse,
    status_code=201,
    summary="Create Ecommerce Tools",
    description="Create get_products and get_orders tools for ecommerce integration"
)
async def create_ecommerce_tools(
    request: CreateEcommerceToolsRequest,
    client: ElevenLabsClient = Depends(get_client)
):
    """
    Create a set of ecommerce tools (get_products, get_orders).
    
    These tools allow agents to fetch product and order information
    during conversations. Make sure your webhook endpoints are accessible.
    """
    try:
        result = client.tools.create_ecommerce_tools(
            webhook_base_url=request.webhook_base_url
        )
        return EcommerceToolsResponse(**result)
        
    except ElevenLabsError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@router.get(
    "",
    response_model=ToolListResponse,
    summary="List Tools",
    description="Get a list of all tools"
)
async def list_tools(
    cursor: Optional[str] = Query(None, description="Pagination cursor"),
    page_size: int = Query(30, ge=1, le=100, description="Results per page"),
    client: ElevenLabsClient = Depends(get_client)
):
    """List all tools with pagination."""
    try:
        result = client.tools.list_tools(cursor=cursor, page_size=page_size)
        return ToolListResponse(
            tools=result.get("tools", []),
            cursor=result.get("cursor")
        )
    except ElevenLabsError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@router.get(
    "/{tool_id}",
    response_model=ToolResponse,
    summary="Get Tool",
    description="Get details of a specific tool",
    responses={404: {"model": ErrorResponse, "description": "Tool not found"}}
)
async def get_tool(
    tool_id: str,
    client: ElevenLabsClient = Depends(get_client)
):
    """Get details of a specific tool by ID."""
    try:
        result = client.tools.get_tool(tool_id)
        return ToolResponse(**result)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ElevenLabsError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@router.delete(
    "/{tool_id}",
    response_model=SuccessResponse,
    summary="Delete Tool",
    description="Delete a tool",
    responses={404: {"model": ErrorResponse, "description": "Tool not found"}}
)
async def delete_tool(
    tool_id: str,
    client: ElevenLabsClient = Depends(get_client)
):
    """Delete a tool by ID."""
    try:
        client.tools.delete_tool(tool_id)
        return SuccessResponse(message=f"Tool {tool_id} deleted successfully")
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ElevenLabsError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))
