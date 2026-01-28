"""
Agent Management Router.
Handles all agent-related API endpoints.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from client import ElevenLabsClient
from api.dependencies import get_client
from api.schemas import (
    CreateAgentRequest,
    CreateAgentResponse,
    AgentResponse,
    AgentListResponse,
    UpdateAgentRequest,
    SuccessResponse,
    ErrorResponse
)
from exceptions import ElevenLabsError, NotFoundError


class UpdateAgentPromptRequest(BaseModel):
    """Request to update agent's prompt configuration."""
    first_message: Optional[str] = Field(None, description="Initial greeting message")
    language: Optional[str] = Field(None, description="Agent language (e.g., 'en', 'it', 'es')")
    system_prompt: Optional[str] = Field(None, description="System prompt defining agent behavior")
    tool_ids: Optional[List[str]] = Field(None, description="List of tool IDs to enable")
    knowledge_base_ids: Optional[List[str]] = Field(None, description="List of knowledge base document IDs")
    
    class Config:
        json_schema_extra = {
            "example": {
                "first_message": "Ciao! Come posso aiutarti oggi?",
                "language": "it",
                "knowledge_base_ids": ["doc123", "doc456"],
                "system_prompt": "Sei un assistente utile per il negozio online."
            }
        }


router = APIRouter(
    prefix="/agents",
    tags=["Agents"],
    responses={
        401: {"model": ErrorResponse, "description": "Authentication failed"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)


@router.post(
    "",
    response_model=CreateAgentResponse,
    status_code=201,
    summary="Create Agent",
    description="Create a new conversational AI agent"
)
async def create_agent(
    request: CreateAgentRequest,
    client: ElevenLabsClient = Depends(get_client)
):
    """
    Create a new agent with the specified configuration.
    
    You can either provide individual fields (name, voice_id, first_message, etc.)
    or a full conversation_config object.
    
    Optionally include tool_ids to enable custom tools for this agent.
    """
    try:
        # If full config provided, use it
        if request.conversation_config:
            result = client.agents.create_agent(
                conversation_config=request.conversation_config.model_dump(exclude_none=True)
            )
        else:
            # Use individual fields
            result = client.agents.create_agent(
                name=request.name,
                voice_id=request.voice_id,
                first_message=request.first_message,
                system_prompt=request.system_prompt,
                language=request.language,
                tool_ids=request.tool_ids,
                knowledge_base_ids=request.knowledge_base_ids
            )
        
        return CreateAgentResponse(agent_id=result["agent_id"])
        
    except ElevenLabsError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@router.get(
    "",
    response_model=AgentListResponse,
    summary="List Agents",
    description="Get a list of all agents with pagination"
)
async def list_agents(
    cursor: Optional[str] = Query(None, description="Pagination cursor"),
    page_size: int = Query(30, ge=1, le=100, description="Number of results per page"),
    client: ElevenLabsClient = Depends(get_client)
):
    """List all agents with optional pagination."""
    try:
        result = client.agents.list_agents(cursor=cursor, page_size=page_size)
        return AgentListResponse(
            agents=result.get("agents", []),
            cursor=result.get("cursor")
        )
    except ElevenLabsError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@router.get(
    "/{agent_id}",
    response_model=AgentResponse,
    summary="Get Agent",
    description="Get details of a specific agent",
    responses={404: {"model": ErrorResponse, "description": "Agent not found"}}
)
async def get_agent(
    agent_id: str,
    client: ElevenLabsClient = Depends(get_client)
):
    """Get details of a specific agent by ID."""
    try:
        result = client.agents.get_agent(agent_id)
        return AgentResponse(**result)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ElevenLabsError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@router.patch(
    "/{agent_id}",
    response_model=AgentResponse,
    summary="Update Agent",
    description="Update an existing agent",
    responses={404: {"model": ErrorResponse, "description": "Agent not found"}}
)
async def update_agent(
    agent_id: str,
    request: UpdateAgentRequest,
    client: ElevenLabsClient = Depends(get_client)
):
    """Update an agent's configuration."""
    try:
        update_data = request.model_dump(exclude_none=True)
        
        # Convert conversation_config if present
        if "conversation_config" in update_data and update_data["conversation_config"]:
            update_data["conversation_config"] = update_data["conversation_config"]
        
        result = client.agents.update_agent(agent_id, **update_data)
        return AgentResponse(**result)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ElevenLabsError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@router.patch(
    "/{agent_id}/prompt",
    response_model=AgentResponse,
    summary="Update Agent Prompt",
    description="Update only the agent's first message, language, and/or system prompt",
    responses={404: {"model": ErrorResponse, "description": "Agent not found"}}
)
async def update_agent_prompt(
    agent_id: str,
    request: UpdateAgentPromptRequest,
    client: ElevenLabsClient = Depends(get_client)
):
    """
    Update an agent's prompt configuration.
    
    This is a convenience endpoint that allows updating:
    - first_message: The initial greeting
    - language: The agent's language
    - system_prompt: The behavior instructions
    - tool_ids: List of tool IDs to enable
    - knowledge_base_ids: List of knowledge base document IDs
    
    Only provided fields will be updated.
    """
    try:
        # Build conversation_config with only the fields provided
        agent_config = {}
        prompt_config = {}
        tts_config = {}
        
        if request.first_message is not None:
            agent_config["first_message"] = request.first_message
        
        if request.language is not None:
            agent_config["language"] = request.language
            # For non-English, ensure multilingual TTS model
            if request.language.lower() != "en":
                tts_config["model_id"] = "eleven_turbo_v2_5"
        
        if request.system_prompt is not None:
            prompt_config["prompt"] = request.system_prompt
        
        # Add tool_ids if provided
        if request.tool_ids is not None:
            prompt_config["tool_ids"] = request.tool_ids
        
        # Add knowledge_base if provided (list of objects with id, type, name)
        if request.knowledge_base_ids is not None:
            prompt_config["knowledge_base"] = [
                {"id": kb_id, "type": "file", "name": f"KB Document {i+1}"} 
                for i, kb_id in enumerate(request.knowledge_base_ids)
            ]
        
        if prompt_config:
            agent_config["prompt"] = prompt_config
        
        conversation_config = {}
        if agent_config:
            conversation_config["agent"] = agent_config
        if tts_config:
            conversation_config["tts"] = tts_config
        
        if not conversation_config:
            raise HTTPException(
                status_code=400, 
                detail="At least one field must be provided: first_message, language, system_prompt, tool_ids, or knowledge_base_ids"
            )
        
        result = client.agents.update_agent(
            agent_id=agent_id,
            conversation_config=conversation_config
        )
        return AgentResponse(**result)
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ElevenLabsError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@router.delete(
    "/{agent_id}",
    response_model=SuccessResponse,
    summary="Delete Agent",
    description="Delete an agent",
    responses={404: {"model": ErrorResponse, "description": "Agent not found"}}
)
async def delete_agent(
    agent_id: str,
    client: ElevenLabsClient = Depends(get_client)
):
    """Delete an agent by ID."""
    try:
        client.agents.delete_agent(agent_id)
        return SuccessResponse(message=f"Agent {agent_id} deleted successfully")
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ElevenLabsError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))
