"""
Tools Service for ElevenLabs API.
Manages custom tools that agents can use during conversations.
"""

from typing import Optional, Dict, Any, List

from base import BaseClient
from config import ElevenLabsConfig
from logger import APICallLogger


class ToolsService(BaseClient):
    """
    Service class for managing ElevenLabs agent tools.
    
    Tools allow agents to interact with external systems during conversations.
    They can make HTTP requests to webhooks to fetch data or perform actions.
    
    Example:
        >>> from config import ElevenLabsConfig
        >>> config = ElevenLabsConfig.from_env()
        >>> tools_service = ToolsService(config)
        >>> tool = tools_service.create_webhook_tool(
        ...     name="get_products",
        ...     description="Fetch products from the store",
        ...     webhook_url="https://your-api.com/webhook/products"
        ... )
    """
    
    # API Endpoints
    TOOLS_ENDPOINT = "/v1/convai/tools"
    
    def __init__(self, config: ElevenLabsConfig):
        """
        Initialize Tools Service.
        
        Args:
            config: ElevenLabsConfig instance
        """
        super().__init__(config, logger_name="elevenlabs.tools")
        self.logger.info("ToolsService initialized")
    
    def create_webhook_tool(
        self,
        name: str,
        description: str,
        webhook_url: str,
        parameters: Optional[List[Dict[str, Any]]] = None,
        http_method: str = "POST",
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a webhook tool that makes HTTP requests during conversations.
        
        API Endpoint: POST /v1/convai/tools
        
        Args:
            name: Tool name (used in function calls)
            description: Description of what the tool does (helps LLM understand when to use it)
            webhook_url: URL to call when tool is invoked
            parameters: List of parameter definitions for the tool
            http_method: HTTP method (GET, POST, etc.)
            headers: Additional headers to send with webhook request
            **kwargs: Additional tool configuration
            
        Returns:
            Created tool details including tool_id
            
        Example:
            >>> tool = service.create_webhook_tool(
            ...     name="get_products",
            ...     description="Fetch products from the ecommerce store. Use when user asks about products, inventory, or catalog.",
            ...     webhook_url="https://api.example.com/webhook/products",
            ...     parameters=[
            ...         {"name": "limit", "type": "integer", "description": "Number of products to fetch", "required": False}
            ...     ]
            ... )
        """
        with APICallLogger(self.logger, "Create Webhook Tool", name=name):
            # Build request body schema for parameters
            request_body_schema = {
                "type": "object",
                "properties": {},
                "required": []
            }
            
            if parameters:
                for param in parameters:
                    param_name = param["name"]
                    prop = {
                        "type": param.get("type", "string")
                    }
                    
                    # ElevenLabs API: Can only set ONE of: description, dynamic_variable, 
                    # is_system_provided, or constant_value
                    if param.get("dynamic_variable"):
                        prop["dynamic_variable"] = param["dynamic_variable"]
                    elif param.get("constant_value"):
                        prop["constant_value"] = param["constant_value"]
                    elif param.get("is_system_provided"):
                        prop["is_system_provided"] = param["is_system_provided"]
                    else:
                        # Only add description if no other special field is set
                        prop["description"] = param.get("description", "")
                    
                    request_body_schema["properties"][param_name] = prop
                    
                    if param.get("required", False):
                        request_body_schema["required"].append(param_name)
            
            # ElevenLabs webhook api_schema format
            # api_schema goes directly under tool_config (not nested in webhook)
            # POST method requires request_body_schema
            api_schema = {
                "url": webhook_url,
                "method": http_method,
                "request_body_schema": request_body_schema  # Required for POST
            }
            
            # Only add headers if provided
            if headers:
                api_schema["request_headers"] = headers
            
            tool_config = {
                "type": "webhook",
                "name": name,
                "description": description,
                "api_schema": api_schema  # api_schema is at tool_config level
            }
            
            payload = {"tool_config": tool_config}
            payload.update(kwargs)
            
            response = self._make_request(
                method="POST",
                endpoint=self.TOOLS_ENDPOINT,
                data=payload
            )
            
            # API returns 'id', normalize to 'tool_id' for consistency
            tool_id = response.get("id") or response.get("tool_id", "unknown")
            response["tool_id"] = tool_id
            self.logger.info(f"Webhook tool created: {tool_id}")
            return response
    
    def create_client_tool(
        self,
        name: str,
        description: str,
        parameters: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a client-side tool (handled by the client application).
        
        Args:
            name: Tool name
            description: Description of what the tool does
            parameters: List of parameter definitions
            **kwargs: Additional configuration
            
        Returns:
            Created tool details
        """
        with APICallLogger(self.logger, "Create Client Tool", name=name):
            tool_config = {
                "type": "client",
                "name": name,
                "description": description
            }
            
            if parameters:
                tool_config["parameters"] = {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
                for param in parameters:
                    param_name = param["name"]
                    tool_config["parameters"]["properties"][param_name] = {
                        "type": param.get("type", "string"),
                        "description": param.get("description", "")
                    }
                    if param.get("required", False):
                        tool_config["parameters"]["required"].append(param_name)
            
            payload = {"tool_config": tool_config}
            payload.update(kwargs)
            
            response = self._make_request(
                method="POST",
                endpoint=self.TOOLS_ENDPOINT,
                data=payload
            )
            
            # API returns 'id', normalize to 'tool_id' for consistency
            tool_id = response.get("id") or response.get("tool_id", "unknown")
            response["tool_id"] = tool_id
            self.logger.info(f"Client tool created: {tool_id}")
            return response
    
    def get_tool(self, tool_id: str) -> Dict[str, Any]:
        """
        Get details of a specific tool.
        
        Args:
            tool_id: Tool identifier
            
        Returns:
            Tool details
        """
        with APICallLogger(self.logger, "Get Tool", tool_id=tool_id):
            response = self._make_request(
                method="GET",
                endpoint=f"{self.TOOLS_ENDPOINT}/{tool_id}"
            )
            
            self.logger.info(f"Retrieved tool: {tool_id}")
            return response
    
    def list_tools(
        self,
        cursor: Optional[str] = None,
        page_size: int = 30
    ) -> Dict[str, Any]:
        """
        List all tools.
        
        Args:
            cursor: Pagination cursor
            page_size: Results per page
            
        Returns:
            List of tools
        """
        with APICallLogger(self.logger, "List Tools"):
            params = {"page_size": page_size}
            if cursor:
                params["cursor"] = cursor
            
            response = self._make_request(
                method="GET",
                endpoint=self.TOOLS_ENDPOINT,
                params=params
            )
            
            count = len(response.get("tools", []))
            self.logger.info(f"Retrieved {count} tools")
            return response
    
    def delete_tool(self, tool_id: str) -> Dict[str, Any]:
        """
        Delete a tool.
        
        Args:
            tool_id: Tool ID to delete
            
        Returns:
            Deletion confirmation
        """
        with APICallLogger(self.logger, "Delete Tool", tool_id=tool_id):
            response = self._make_request(
                method="DELETE",
                endpoint=f"{self.TOOLS_ENDPOINT}/{tool_id}"
            )
            
            self.logger.info(f"Deleted tool: {tool_id}")
            return response
    
    def create_ecommerce_tools(
        self,
        webhook_base_url: str,
        conversation_id_param: str = "conversation_id"
    ) -> Dict[str, Any]:
        """
        Create a set of ecommerce tools (get_products, get_orders).
        
        This is a convenience method that creates both product and order tools.
        
        Args:
            webhook_base_url: Base URL for webhook endpoints (e.g., https://your-api.com/api/v1)
            conversation_id_param: Parameter name to pass conversation ID
            
        Returns:
            Dict with created tool IDs
        """
        # Remove trailing slash to avoid double slashes
        base_url = webhook_base_url.rstrip('/')
        
        # Common parameters for ecommerce tools - include conversation_id for credential lookup
        common_params = [
            {
                "name": "conversation_id",
                "type": "string",
                "description": "Conversation identifier for credential lookup",
                "required": True,
                "dynamic_variable": "system__conversation_id"  # Auto-filled by ElevenLabs
            },
            {
                "name": "limit",
                "type": "integer",
                "description": "Number of items to fetch (1-20)",
                "required": False
            }
        ]
        
        products_tool = self.create_webhook_tool(
            name="get_products",
            description="Fetch products from the ecommerce store. Use this when the user asks about products, inventory, catalog, what items are available, or pricing information.",
            webhook_url=f"{base_url}/webhook/ecommerce/products",
            parameters=common_params
        )
        
        orders_tool = self.create_webhook_tool(
            name="get_orders",
            description="Fetch recent orders from the ecommerce store. Use this when the user asks about their orders, order status, order history, or shipment tracking.",
            webhook_url=f"{base_url}/webhook/ecommerce/orders",
            parameters=common_params
        )
        
        return {
            "products_tool_id": products_tool.get("tool_id"),
            "orders_tool_id": orders_tool.get("tool_id")
        }
