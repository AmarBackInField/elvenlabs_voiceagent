"""
Conversations Router.
Handles conversation history, transcripts, and recordings.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from client import ElevenLabsClient
from api.dependencies import get_client
from api.schemas import (
    ConversationResponse,
    ConversationListResponse,
    SuccessResponse,
    ErrorResponse
)
from exceptions import ElevenLabsError, NotFoundError


router = APIRouter(
    prefix="/conversations",
    tags=["Conversations"],
    responses={
        401: {"model": ErrorResponse, "description": "Authentication failed"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)


@router.get(
    "",
    response_model=ConversationListResponse,
    summary="List Conversations",
    description="Get a list of all conversations with optional filtering"
)
async def list_conversations(
    agent_id: Optional[str] = Query(None, description="Filter by agent ID"),
    cursor: Optional[str] = Query(None, description="Pagination cursor"),
    page_size: int = Query(30, ge=1, le=100, description="Results per page"),
    client: ElevenLabsClient = Depends(get_client)
):
    """
    List all conversations with pagination.
    
    Optionally filter by agent_id to see conversations for a specific agent.
    """
    try:
        result = client.conversations.list_conversations(
            agent_id=agent_id,
            cursor=cursor,
            page_size=page_size
        )
        return ConversationListResponse(
            conversations=result.get("conversations", []),
            cursor=result.get("cursor")
        )
    except ElevenLabsError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@router.get(
    "/{conversation_id}",
    response_model=ConversationResponse,
    summary="Get Conversation",
    description="Get conversation details including transcript",
    responses={404: {"model": ErrorResponse, "description": "Conversation not found"}}
)
async def get_conversation(
    conversation_id: str,
    client: ElevenLabsClient = Depends(get_client)
):
    """
    Get details of a specific conversation.
    
    Returns full conversation details including:
    - Transcript with all messages
    - Call metadata (duration, timestamps)
    - Agent information
    """
    try:
        result = client.conversations.get_conversation(conversation_id)
        return ConversationResponse(**result)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ElevenLabsError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@router.get(
    "/{conversation_id}/audio",
    summary="Get Conversation Audio",
    description="Download the audio recording of a conversation",
    responses={
        200: {
            "content": {"audio/mpeg": {}},
            "description": "Audio file (MP3)"
        },
        404: {"model": ErrorResponse, "description": "Conversation not found"}
    }
)
async def get_conversation_audio(
    conversation_id: str,
    client: ElevenLabsClient = Depends(get_client)
):
    """
    Download the audio recording of a conversation.
    
    Returns the audio file as MP3 format.
    """
    try:
        audio_bytes = client.conversations.get_conversation_audio(conversation_id)
        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f"attachment; filename=conversation_{conversation_id}.mp3"
            }
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ElevenLabsError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@router.delete(
    "/{conversation_id}",
    response_model=SuccessResponse,
    summary="Delete Conversation",
    description="Delete a conversation and its data",
    responses={404: {"model": ErrorResponse, "description": "Conversation not found"}}
)
async def delete_conversation(
    conversation_id: str,
    client: ElevenLabsClient = Depends(get_client)
):
    """Delete a conversation by ID."""
    try:
        client.conversations.delete_conversation(conversation_id)
        return SuccessResponse(message=f"Conversation {conversation_id} deleted successfully")
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ElevenLabsError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))
