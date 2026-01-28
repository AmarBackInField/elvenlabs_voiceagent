"""
Knowledge Base Router.
Handles document ingestion from text, URL, or file.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from enum import Enum

from client import ElevenLabsClient
from api.dependencies import get_client
from api.schemas import (
    KnowledgeBaseDocumentResponse,
    KnowledgeBaseListResponse,
    IngestTextRequest,
    IngestURLRequest,
    SuccessResponse,
    ErrorResponse
)
from exceptions import ElevenLabsError, NotFoundError


class SourceType(str, Enum):
    """Source type for document ingestion."""
    text = "text"
    url = "url"
    file = "file"


router = APIRouter(
    prefix="/knowledge-base",
    tags=["Knowledge Base"],
    responses={
        401: {"model": ErrorResponse, "description": "Authentication failed"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)


@router.post(
    "/ingest",
    response_model=KnowledgeBaseDocumentResponse,
    status_code=201,
    summary="Ingest Document (Unified)",
    description="Ingest a document from text, URL, or file upload"
)
async def ingest_document(
    source_type: SourceType = Form(..., description="Source type: text, url, or file"),
    name: Optional[str] = Form(None, description="Custom document name"),
    parent_folder_id: Optional[str] = Form(None, description="Folder to place document in"),
    text: Optional[str] = Form(None, description="Text content (required if source_type=text)"),
    url: Optional[str] = Form(None, description="URL to scrape (required if source_type=url)"),
    file: Optional[UploadFile] = File(None, description="File to upload (required if source_type=file)"),
    client: ElevenLabsClient = Depends(get_client)
):
    """
    Unified endpoint to ingest documents into the knowledge base.
    
    Supports three source types:
    - **text**: Provide text content directly
    - **url**: Scrape content from a webpage
    - **file**: Upload a document file (PDF, TXT, MD, DOCX)
    
    Examples:
    
    **Ingest from text:**
    ```
    curl -X POST "/ingest" -F "source_type=text" -F "text=Your content here" -F "name=My Document"
    ```
    
    **Ingest from URL:**
    ```
    curl -X POST "/ingest" -F "source_type=url" -F "url=https://example.com/page"
    ```
    
    **Ingest from file:**
    ```
    curl -X POST "/ingest" -F "source_type=file" -F "file=@document.pdf"
    ```
    """
    try:
        if source_type == SourceType.text:
            if not text:
                raise HTTPException(
                    status_code=422,
                    detail="Text content is required when source_type is 'text'"
                )
            result = client.knowledge_base.create_from_text(
                text=text,
                name=name,
                parent_folder_id=parent_folder_id
            )
            result["source_type"] = "text"
            
        elif source_type == SourceType.url:
            if not url:
                raise HTTPException(
                    status_code=422,
                    detail="URL is required when source_type is 'url'"
                )
            result = client.knowledge_base.create_from_url(
                url=url,
                name=name,
                parent_folder_id=parent_folder_id
            )
            result["source_type"] = "url"
            
        elif source_type == SourceType.file:
            if not file:
                raise HTTPException(
                    status_code=422,
                    detail="File is required when source_type is 'file'"
                )
            file_content = await file.read()
            result = client.knowledge_base.create_from_file(
                file_content=file_content,
                filename=file.filename,
                name=name,
                parent_folder_id=parent_folder_id
            )
            result["source_type"] = "file"
        
        # Normalize response fields
        result["document_id"] = result.get("id") or result.get("document_id")
        return KnowledgeBaseDocumentResponse(**result)
        
    except ElevenLabsError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@router.post(
    "/text",
    response_model=KnowledgeBaseDocumentResponse,
    status_code=201,
    summary="Ingest from Text",
    description="Create a knowledge base document from text content"
)
async def ingest_from_text(
    request: IngestTextRequest,
    client: ElevenLabsClient = Depends(get_client)
):
    """Create a knowledge base document from text content."""
    try:
        result = client.knowledge_base.create_from_text(
            text=request.text,
            name=request.name,
            parent_folder_id=request.parent_folder_id
        )
        # Normalize response fields
        result["document_id"] = result.get("id") or result.get("document_id")
        result["source_type"] = "text"
        return KnowledgeBaseDocumentResponse(**result)
        
    except ElevenLabsError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@router.post(
    "/url",
    response_model=KnowledgeBaseDocumentResponse,
    status_code=201,
    summary="Ingest from URL",
    description="Create a knowledge base document by scraping a webpage"
)
async def ingest_from_url(
    request: IngestURLRequest,
    client: ElevenLabsClient = Depends(get_client)
):
    """Create a knowledge base document by scraping a URL."""
    try:
        result = client.knowledge_base.create_from_url(
            url=request.url,
            name=request.name,
            parent_folder_id=request.parent_folder_id
        )
        # Normalize response fields
        result["document_id"] = result.get("id") or result.get("document_id")
        result["source_type"] = "url"
        return KnowledgeBaseDocumentResponse(**result)
        
    except ElevenLabsError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@router.post(
    "/file",
    response_model=KnowledgeBaseDocumentResponse,
    status_code=201,
    summary="Ingest from File",
    description="Create a knowledge base document from an uploaded file"
)
async def ingest_from_file(
    file: UploadFile = File(..., description="File to upload (PDF, TXT, MD, DOCX)"),
    name: Optional[str] = Form(None, description="Custom document name"),
    parent_folder_id: Optional[str] = Form(None, description="Folder to place document in"),
    client: ElevenLabsClient = Depends(get_client)
):
    """
    Create a knowledge base document from an uploaded file.
    
    Supported file types: PDF, TXT, MD, DOCX
    """
    try:
        file_content = await file.read()
        result = client.knowledge_base.create_from_file(
            file_content=file_content,
            filename=file.filename,
            name=name,
            parent_folder_id=parent_folder_id
        )
        # Normalize response fields
        result["document_id"] = result.get("id") or result.get("document_id")
        result["source_type"] = "file"
        return KnowledgeBaseDocumentResponse(**result)
        
    except ElevenLabsError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@router.get(
    "",
    response_model=KnowledgeBaseListResponse,
    summary="List Documents",
    description="Get a list of all knowledge base documents"
)
async def list_documents(
    cursor: Optional[str] = Query(None, description="Pagination cursor"),
    page_size: int = Query(30, ge=1, le=100, description="Results per page"),
    client: ElevenLabsClient = Depends(get_client)
):
    """List all knowledge base documents with pagination."""
    try:
        result = client.knowledge_base.list_documents(cursor=cursor, page_size=page_size)
        return KnowledgeBaseListResponse(
            documents=result.get("documents", []),
            cursor=result.get("cursor")
        )
    except ElevenLabsError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@router.get(
    "/{document_id}",
    response_model=KnowledgeBaseDocumentResponse,
    summary="Get Document",
    description="Get details of a knowledge base document",
    responses={404: {"model": ErrorResponse, "description": "Document not found"}}
)
async def get_document(
    document_id: str,
    client: ElevenLabsClient = Depends(get_client)
):
    """Get details of a specific knowledge base document."""
    try:
        result = client.knowledge_base.get_document(document_id)
        return KnowledgeBaseDocumentResponse(**result)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ElevenLabsError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))


@router.delete(
    "/{document_id}",
    response_model=SuccessResponse,
    summary="Delete Document",
    description="Delete a knowledge base document",
    responses={404: {"model": ErrorResponse, "description": "Document not found"}}
)
async def delete_document(
    document_id: str,
    client: ElevenLabsClient = Depends(get_client)
):
    """Delete a knowledge base document."""
    try:
        client.knowledge_base.delete_document(document_id)
        return SuccessResponse(message=f"Document {document_id} deleted successfully")
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ElevenLabsError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))
