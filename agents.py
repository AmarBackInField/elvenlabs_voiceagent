"""
Agent Management Service for ElevenLabs API.
Handles all agent-related operations.
"""

from typing import Optional, Dict, Any, List

from base import BaseClient
from config import ElevenLabsConfig
from logger import APICallLogger


class AgentService(BaseClient):
    """
    Service class for managing ElevenLabs conversational AI agents.
    
    Provides methods for:
    - Creating agents
    - Getting agent details
    - Listing agents
    - Updating agents
    - Deleting agents
    
    Example:
        >>> from config import ElevenLabsConfig
        >>> config = ElevenLabsConfig.from_env()
        >>> agent_service = AgentService(config)
        >>> agent = agent_service.create_agent(
        ...     conversation_config={"agent": {"first_message": "Hello!"}}
        ... )
    """
    
    # API Endpoints (as per official documentation)
    CREATE_AGENT_ENDPOINT = "/v1/convai/agents/create"
    AGENTS_ENDPOINT = "/v1/convai/agents"
    
    def __init__(self, config: ElevenLabsConfig):
        """
        Initialize Agent Service.
        
        Args:
            config: ElevenLabsConfig instance
        """
        super().__init__(config, logger_name="elevenlabs.agents")
        self.logger.info("AgentService initialized")
    
    def create_agent(
        self,
        conversation_config: Optional[Dict[str, Any]] = None,
        name: Optional[str] = None,
        voice_id: Optional[str] = None,
        first_message: Optional[str] = None,
        system_prompt: Optional[str] = None,
        language: str = "en",
        tool_ids: Optional[List[str]] = None,
        knowledge_base_ids: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a new conversational AI agent.
        
        API Endpoint: POST /v1/convai/agents/create
        
        Args:
            conversation_config: Full conversation configuration object.
                                If provided, other params are ignored.
            name: Agent name (used if conversation_config not provided)
            voice_id: Voice ID for TTS (used if conversation_config not provided)
            first_message: Initial greeting message
            system_prompt: System prompt defining agent behavior
            language: Agent language (default: "en")
            tool_ids: List of tool IDs to enable for this agent
            **kwargs: Additional configuration options
            
        Returns:
            Response containing agent_id
            
        Example:
            >>> # Using conversation_config directly
            >>> agent = service.create_agent(
            ...     conversation_config={
            ...         "agent": {"first_message": "Hello!"},
            ...         "tts": {"voice_id": "21m00Tcm4TlvDq8ikWAM"}
            ...     }
            ... )
            
            >>> # Using helper parameters with tools
            >>> agent = service.create_agent(
            ...     name="My Agent",
            ...     voice_id="21m00Tcm4TlvDq8ikWAM",
            ...     first_message="Hello! How can I help?",
            ...     tool_ids=["tool_abc123", "tool_xyz789"]
            ... )
        """
        with APICallLogger(self.logger, "Create Agent"):
            # If full config provided, use it directly
            if conversation_config is not None:
                payload = {"conversation_config": conversation_config}
            else:
                # Build config from helper parameters
                agent_config = {
                    "first_message": first_message or "",
                    "language": language
                }
                
                # Build prompt config with system prompt, tools, and knowledge base
                prompt_config = {}
                if system_prompt:
                    prompt_config["prompt"] = system_prompt
                
                # Add tools to prompt config (tool_ids is a list of strings)
                if tool_ids:
                    prompt_config["tool_ids"] = tool_ids
                
                # Add knowledge base documents (list of objects with id, type, and name)
                # Type can be: 'file', 'url', 'text', or 'folder'
                if knowledge_base_ids:
                    prompt_config["knowledge_base"] = [
                        {"id": kb_id, "type": "file", "name": f"KB Document {i+1}"} 
                        for i, kb_id in enumerate(knowledge_base_ids)
                    ]
                
                if prompt_config:
                    agent_config["prompt"] = prompt_config
                
                tts_config = {}
                if voice_id:
                    tts_config["voice_id"] = voice_id
                
                # For non-English languages, use multilingual TTS model
                if language and language.lower() != "en":
                    tts_config["model_id"] = "eleven_turbo_v2_5"
                
                payload = {
                    "conversation_config": {
                        "agent": agent_config,
                        "tts": tts_config
                    }
                }
                
                if name:
                    payload["name"] = name
            
            # Merge additional kwargs
            payload.update(kwargs)
            
            response = self._make_request(
                method="POST",
                endpoint=self.CREATE_AGENT_ENDPOINT,
                data=payload
            )
            
            agent_id = response.get("agent_id", "unknown")
            self.logger.info(f"Agent created successfully: {agent_id}")
            return response
    
    def get_agent(self, agent_id: str) -> Dict[str, Any]:
        """
        Get details of a specific agent.
        
        API Endpoint: GET /v1/convai/agents/{agent_id}
        
        Args:
            agent_id: Unique agent identifier
            
        Returns:
            Agent details including full configuration
            
        Raises:
            NotFoundError: If agent doesn't exist
            
        Example:
            >>> agent = service.get_agent("J3Pbu5gP6NNKBscdCdwB")
            >>> print(agent["name"])
        """
        with APICallLogger(self.logger, "Get Agent", agent_id=agent_id):
            response = self._make_request(
                method="GET",
                endpoint=f"{self.AGENTS_ENDPOINT}/{agent_id}"
            )
            
            self.logger.info(f"Retrieved agent: {agent_id}")
            return response
    
    def list_agents(
        self,
        cursor: Optional[str] = None,
        page_size: int = 30
    ) -> Dict[str, Any]:
        """
        List all agents with pagination.
        
        API Endpoint: GET /v1/convai/agents
        
        Args:
            cursor: Pagination cursor for next page
            page_size: Number of agents per page (default: 30)
            
        Returns:
            List of agents with pagination info
            
        Example:
            >>> result = service.list_agents(page_size=10)
            >>> for agent in result.get("agents", []):
            ...     print(agent["agent_id"], agent.get("name"))
        """
        with APICallLogger(self.logger, "List Agents"):
            params = {"page_size": page_size}
            if cursor:
                params["cursor"] = cursor
            
            response = self._make_request(
                method="GET",
                endpoint=self.AGENTS_ENDPOINT,
                params=params
            )
            
            agent_count = len(response.get("agents", []))
            self.logger.info(f"Retrieved {agent_count} agents")
            return response
    
    def update_agent(
        self,
        agent_id: str,
        conversation_config: Optional[Dict[str, Any]] = None,
        **updates
    ) -> Dict[str, Any]:
        """
        Update an existing agent.
        
        API Endpoint: PATCH /v1/convai/agents/{agent_id}
        
        Args:
            agent_id: Agent ID to update
            conversation_config: Updated conversation configuration
            **updates: Additional fields to update
            
        Returns:
            Updated agent details
            
        Example:
            >>> service.update_agent(
            ...     "J3Pbu5gP6NNKBscdCdwB",
            ...     conversation_config={"agent": {"first_message": "New greeting!"}}
            ... )
        """
        with APICallLogger(self.logger, "Update Agent", agent_id=agent_id):
            payload = {}
            
            if conversation_config:
                payload["conversation_config"] = conversation_config
            
            payload.update(updates)
            
            response = self._make_request(
                method="PATCH",
                endpoint=f"{self.AGENTS_ENDPOINT}/{agent_id}",
                data=payload
            )
            
            self.logger.info(f"Agent updated: {agent_id}")
            return response
    
    def delete_agent(self, agent_id: str) -> Dict[str, Any]:
        """
        Delete an agent.
        
        API Endpoint: DELETE /v1/convai/agents/{agent_id}
        
        Args:
            agent_id: Agent ID to delete
            
        Returns:
            Deletion confirmation
            
        Raises:
            NotFoundError: If agent doesn't exist
            
        Example:
            >>> service.delete_agent("J3Pbu5gP6NNKBscdCdwB")
        """
        with APICallLogger(self.logger, "Delete Agent", agent_id=agent_id):
            response = self._make_request(
                method="DELETE",
                endpoint=f"{self.AGENTS_ENDPOINT}/{agent_id}"
            )
            
            self.logger.info(f"Agent deleted: {agent_id}")
            return response
