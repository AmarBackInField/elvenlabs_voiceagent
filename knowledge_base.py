"""
Knowledge Base Service for ElevenLabs API.
Handles document ingestion from text, URL, or file.
"""

from typing import Optional, Dict, Any

from base import BaseClient
from config import ElevenLabsConfig
from logger import APICallLogger


class KnowledgeBaseService(BaseClient):
    """
    Service class for managing ElevenLabs knowledge base documents.
    
    Provides methods for:
    - Creating documents from text
    - Creating documents from URL
    - Creating documents from file upload
    - Listing and managing documents
    
    Example:
        >>> from config import ElevenLabsConfig
        >>> config = ElevenLabsConfig.from_env()
        >>> kb_service = KnowledgeBaseService(config)
        >>> doc = kb_service.create_from_text(
        ...     text="Product FAQ content...",
        ...     name="Product FAQ"
        ... )
    """
    
    # API Endpoints
    KB_BASE_ENDPOINT = "/v1/convai/knowledge-base"
    KB_TEXT_ENDPOINT = "/v1/convai/knowledge-base/text"
    KB_URL_ENDPOINT = "/v1/convai/knowledge-base/url"
    KB_FILE_ENDPOINT = "/v1/convai/knowledge-base/file"
    
    def __init__(self, config: ElevenLabsConfig):
        """
        Initialize Knowledge Base Service.
        
        Args:
            config: ElevenLabsConfig instance
        """
        super().__init__(config, logger_name="elevenlabs.knowledge_base")
        self.logger.info("KnowledgeBaseService initialized")
    
    def create_from_text(
        self,
        text: str,
        name: Optional[str] = None,
        parent_folder_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a knowledge base document from text content.
        
        API Endpoint: POST /v1/convai/knowledge-base/text
        
        Args:
            text: The text content for the document
            name: Optional custom name for the document
            parent_folder_id: Optional folder ID to place document in
            
        Returns:
            Response containing:
            - document_id: Unique document identifier
            - name: Document name
            - folder_path: Path to the document
            
        Example:
            >>> doc = service.create_from_text(
            ...     text="Our return policy allows...",
            ...     name="Return Policy"
            ... )
            >>> print(doc["document_id"])
        """
        with APICallLogger(self.logger, "Create KB Document from Text"):
            payload = {"text": text}
            
            if name:
                payload["name"] = name
            if parent_folder_id:
                payload["parent_folder_id"] = parent_folder_id
            
            response = self._make_request(
                method="POST",
                endpoint=self.KB_TEXT_ENDPOINT,
                data=payload
            )
            
            doc_id = response.get("document_id", "unknown")
            self.logger.info(f"KB document created from text: {doc_id}")
            return response
    
    def create_from_url(
        self,
        url: str,
        name: Optional[str] = None,
        parent_folder_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a knowledge base document by scraping a URL.
        
        API Endpoint: POST /v1/convai/knowledge-base/url
        
        Args:
            url: The webpage URL to scrape
            name: Optional custom name for the document
            parent_folder_id: Optional folder ID to place document in
            
        Returns:
            Response containing:
            - document_id: Unique document identifier
            - name: Document name
            - folder_path: Path to the document
            
        Example:
            >>> doc = service.create_from_url(
            ...     url="https://example.com/faq",
            ...     name="FAQ Page"
            ... )
        """
        with APICallLogger(self.logger, "Create KB Document from URL", url=url):
            payload = {"url": url}
            
            if name:
                payload["name"] = name
            if parent_folder_id:
                payload["parent_folder_id"] = parent_folder_id
            
            response = self._make_request(
                method="POST",
                endpoint=self.KB_URL_ENDPOINT,
                data=payload
            )
            
            doc_id = response.get("document_id", "unknown")
            self.logger.info(f"KB document created from URL: {doc_id}")
            return response
    
    def create_from_file(
        self,
        file_content: bytes,
        filename: str,
        name: Optional[str] = None,
        parent_folder_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a knowledge base document from a file upload.
        
        API Endpoint: POST /v1/convai/knowledge-base/file
        
        Args:
            file_content: The file content as bytes
            filename: Original filename (used for content-type detection)
            name: Optional custom name for the document
            parent_folder_id: Optional folder ID to place document in
            
        Returns:
            Response containing:
            - document_id: Unique document identifier
            - name: Document name
            - folder_path: Path to the document
            
        Supported file types:
            - PDF (.pdf)
            - Text (.txt)
            - Markdown (.md)
            - Word documents (.docx)
            
        Example:
            >>> with open("manual.pdf", "rb") as f:
            ...     doc = service.create_from_file(
            ...         file_content=f.read(),
            ...         filename="manual.pdf",
            ...         name="Product Manual"
            ...     )
        """
        with APICallLogger(self.logger, "Create KB Document from File", filename=filename):
            url = f"{self.config.base_url}{self.KB_FILE_ENDPOINT}"
            
            # Determine content type based on file extension
            import mimetypes
            content_type, _ = mimetypes.guess_type(filename)
            if not content_type:
                content_type = "application/octet-stream"
            
            # Prepare multipart form data with explicit content type
            files = {
                "file": (filename, file_content, content_type)
            }
            
            data = {}
            if name:
                data["name"] = name
            if parent_folder_id:
                data["parent_folder_id"] = parent_folder_id
            
            # Use custom headers without Content-Type (let requests set it for multipart)
            headers = {
                "xi-api-key": self.config.api_key,
                "Accept": "application/json"
            }
            
            response = self.session.post(
                url,
                files=files,
                data=data if data else None,
                headers=headers,
                timeout=self.config.timeout
            )
            
            if not response.ok:
                from exceptions import raise_for_status
                try:
                    response_data = response.json()
                except ValueError:
                    response_data = {"error": response.text}
                raise_for_status(response.status_code, response_data)
            
            result = response.json()
            doc_id = result.get("document_id", "unknown")
            self.logger.info(f"KB document created from file: {doc_id}")
            return result
    
    def get_document(self, document_id: str) -> Dict[str, Any]:
        """
        Get details of a knowledge base document.
        
        Args:
            document_id: Document identifier
            
        Returns:
            Document details
        """
        with APICallLogger(self.logger, "Get KB Document", document_id=document_id):
            response = self._make_request(
                method="GET",
                endpoint=f"{self.KB_BASE_ENDPOINT}/{document_id}"
            )
            
            self.logger.info(f"Retrieved KB document: {document_id}")
            return response
    
    def list_documents(
        self,
        cursor: Optional[str] = None,
        page_size: int = 30
    ) -> Dict[str, Any]:
        """
        List all knowledge base documents.
        
        Args:
            cursor: Pagination cursor
            page_size: Results per page
            
        Returns:
            List of documents with pagination
        """
        with APICallLogger(self.logger, "List KB Documents"):
            params = {"page_size": page_size}
            if cursor:
                params["cursor"] = cursor
            
            response = self._make_request(
                method="GET",
                endpoint=self.KB_BASE_ENDPOINT,
                params=params
            )
            
            count = len(response.get("documents", []))
            self.logger.info(f"Retrieved {count} KB documents")
            return response
    
    def delete_document(self, document_id: str) -> Dict[str, Any]:
        """
        Delete a knowledge base document.
        
        Args:
            document_id: Document ID to delete
            
        Returns:
            Deletion confirmation
        """
        with APICallLogger(self.logger, "Delete KB Document", document_id=document_id):
            response = self._make_request(
                method="DELETE",
                endpoint=f"{self.KB_BASE_ENDPOINT}/{document_id}"
            )
            
            self.logger.info(f"Deleted KB document: {document_id}")
            return response
