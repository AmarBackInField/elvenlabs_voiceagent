"""
Email Template Service.
Manages email templates and creates corresponding ElevenLabs webhook tools.
"""

import uuid
import re
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from datetime import datetime
import logging
import requests

from config import ElevenLabsConfig
from tools import ToolsService


logger = logging.getLogger(__name__)


@dataclass
class EmailTemplateParameter:
    """Parameter definition for email template."""
    name: str
    description: str
    required: bool = True


@dataclass
class EmailTemplate:
    """Email template definition."""
    template_id: str
    name: str
    description: str
    subject_template: str
    body_template: str
    parameters: List[EmailTemplateParameter] = field(default_factory=list)
    tool_id: Optional[str] = None  # ElevenLabs tool ID once created
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "template_id": self.template_id,
            "name": self.name,
            "description": self.description,
            "subject_template": self.subject_template,
            "body_template": self.body_template,
            "parameters": [asdict(p) for p in self.parameters],
            "tool_id": self.tool_id,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EmailTemplate":
        """Create from dictionary."""
        params = [EmailTemplateParameter(**p) for p in data.get("parameters", [])]
        return cls(
            template_id=data["template_id"],
            name=data["name"],
            description=data["description"],
            subject_template=data["subject_template"],
            body_template=data["body_template"],
            parameters=params,
            tool_id=data.get("tool_id"),
            created_at=data.get("created_at", datetime.utcnow().isoformat())
        )


class CustomerSessionStore:
    """
    In-memory store for customer session data.
    Maps conversation_id to customer info (name, email, etc.)
    """
    
    def __init__(self):
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger(f"{__name__}.CustomerSessionStore")
    
    def store(self, conversation_id: str, customer_info: Dict[str, Any]) -> None:
        """Store customer info for a conversation."""
        self._sessions[conversation_id] = {
            **customer_info,
            "stored_at": datetime.utcnow().isoformat()
        }
        self.logger.info(f"Stored customer info for conversation {conversation_id}")
    
    def get(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get customer info for a conversation."""
        return self._sessions.get(conversation_id)
    
    def remove(self, conversation_id: str) -> None:
        """Remove customer session."""
        if conversation_id in self._sessions:
            del self._sessions[conversation_id]
            self.logger.info(f"Removed session for conversation {conversation_id}")
    
    def list_all(self) -> Dict[str, Dict[str, Any]]:
        """List all sessions (for debugging)."""
        return self._sessions.copy()


class EmailTemplateService:
    """
    Service for managing email templates and creating webhook tools.
    """
    
    def __init__(self, config: ElevenLabsConfig, webhook_base_url: str):
        """
        Initialize email template service.
        
        Args:
            config: ElevenLabs configuration
            webhook_base_url: Base URL for webhooks (e.g., https://your-ngrok.ngrok-free.app/api/v1)
        """
        self.config = config
        self.webhook_base_url = webhook_base_url.rstrip("/")
        self.tools_service = ToolsService(config)
        self.logger = logging.getLogger(f"{__name__}.EmailTemplateService")
        
        # In-memory template storage (use database in production)
        self._templates: Dict[str, EmailTemplate] = {}
    
    def _extract_placeholders(self, template: str) -> List[str]:
        """Extract placeholder names from template string."""
        # Match {{placeholder}} or {placeholder}
        pattern = r'\{\{?\s*(\w+)\s*\}?\}'
        return list(set(re.findall(pattern, template)))
    
    def _fill_template(self, template: str, values: Dict[str, Any]) -> str:
        """Fill template placeholders with values."""
        result = template
        for key, value in values.items():
            # Replace both {{key}} and {key}
            result = re.sub(r'\{\{\s*' + key + r'\s*\}\}', str(value), result)
            result = re.sub(r'\{\s*' + key + r'\s*\}', str(value), result)
        return result
    
    def create_template(
        self,
        name: str,
        description: str,
        subject_template: str,
        body_template: str,
        parameters: Optional[List[Dict[str, Any]]] = None,
        auto_create_tool: bool = True
    ) -> EmailTemplate:
        """
        Create an email template and optionally create the corresponding webhook tool.
        
        Args:
            name: Template name (also used as tool name, e.g., "confirm_appointment")
            description: Description for when AI should use this tool
            subject_template: Email subject with placeholders like {{date}}
            body_template: Email body with placeholders
            parameters: List of parameter definitions. If not provided, auto-extracted from templates
            auto_create_tool: Whether to auto-create ElevenLabs webhook tool
            
        Returns:
            Created EmailTemplate
        """
        # Generate template ID
        template_id = name.lower().replace(" ", "_").replace("-", "_")
        
        # Auto-extract parameters if not provided
        if parameters is None:
            # Extract from both subject and body
            all_placeholders = set(self._extract_placeholders(subject_template))
            all_placeholders.update(self._extract_placeholders(body_template))
            
            # Remove customer_name and customer_email as they come from session
            session_fields = {"customer_name", "customer_email", "name", "email"}
            tool_placeholders = all_placeholders - session_fields
            
            parameters = [
                {"name": p, "description": f"Value for {p}", "required": True}
                for p in sorted(tool_placeholders)
            ]
        
        # Create parameter objects
        param_objects = [EmailTemplateParameter(**p) for p in parameters]
        
        # Create template
        template = EmailTemplate(
            template_id=template_id,
            name=name,
            description=description,
            subject_template=subject_template,
            body_template=body_template,
            parameters=param_objects
        )
        
        # Create ElevenLabs webhook tool if requested
        if auto_create_tool:
            tool_id = self._create_webhook_tool(template)
            template.tool_id = tool_id
        
        # Store template
        self._templates[template_id] = template
        self.logger.info(f"Created email template: {template_id} with tool_id: {template.tool_id}")
        
        return template
    
    def _create_webhook_tool(self, template: EmailTemplate) -> str:
        """Create ElevenLabs webhook tool for this template."""
        webhook_url = f"{self.webhook_base_url}/webhook/email/{template.template_id}"
        
        # Build parameters for the tool
        # Always include conversation_id as dynamic variable
        tool_parameters = [
            {
                "name": "conversation_id",
                "type": "string",
                "description": "Conversation ID",
                "required": True,
                "dynamic_variable": "system__conversation_id"
            }
        ]
        
        # Add template parameters
        for param in template.parameters:
            tool_parameters.append({
                "name": param.name,
                "type": "string",
                "description": param.description,
                "required": param.required
            })
        
        # Create the webhook tool
        result = self.tools_service.create_webhook_tool(
            name=template.template_id,
            description=template.description,
            webhook_url=webhook_url,
            http_method="POST",
            parameters=tool_parameters
        )
        
        return result.get("tool_id", result.get("id"))
    
    def get_template(self, template_id: str) -> Optional[EmailTemplate]:
        """Get a template by ID."""
        return self._templates.get(template_id)
    
    def list_templates(self) -> List[EmailTemplate]:
        """List all templates."""
        return list(self._templates.values())
    
    def delete_template(self, template_id: str) -> bool:
        """Delete a template."""
        if template_id in self._templates:
            template = self._templates[template_id]
            
            # Try to delete the associated tool (may fail if in use)
            if template.tool_id:
                try:
                    self.tools_service.delete_tool(template.tool_id)
                except Exception as e:
                    self.logger.warning(f"Could not delete tool {template.tool_id}: {e}")
            
            del self._templates[template_id]
            self.logger.info(f"Deleted email template: {template_id}")
            return True
        return False
    
    def send_email(
        self,
        template_id: str,
        customer_info: Dict[str, Any],
        parameters: Dict[str, Any],
        email_api_url: str = "https://keplerov1-python-2.onrender.com/email/send",
        user_email: str = "amarc8399@gmail.com"
    ) -> Dict[str, Any]:
        """
        Send email using a template.
        
        Args:
            template_id: Template to use
            customer_info: Customer info with 'name' and 'email'
            parameters: Values for template placeholders
            email_api_url: External email API URL
            user_email: x-user-email header value
            
        Returns:
            API response
        """
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")
        
        # Merge customer info with parameters
        all_values = {
            "customer_name": customer_info.get("name", customer_info.get("customer_name", "")),
            "customer_email": customer_info.get("email", customer_info.get("customer_email", "")),
            "name": customer_info.get("name", customer_info.get("customer_name", "")),
            "email": customer_info.get("email", customer_info.get("customer_email", "")),
            **parameters
        }
        
        # Fill templates
        subject = self._fill_template(template.subject_template, all_values)
        body = self._fill_template(template.body_template, all_values)
        
        # Get recipient email
        to_email = customer_info.get("email", customer_info.get("customer_email"))
        if not to_email:
            raise ValueError("Customer email not found in customer_info")
        
        # Send via external API
        payload = {
            "to": to_email,
            "subject": subject,
            "body": body
        }
        
        headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
            "x-user-email": user_email
        }
        
        self.logger.info(f"Sending email to {to_email} using template {template_id}")
        self.logger.debug(f"Subject: {subject}")
        
        response = requests.post(email_api_url, json=payload, headers=headers, timeout=30)
        
        if response.ok:
            self.logger.info(f"Email sent successfully to {to_email}")
            return {"success": True, "message": f"Email sent to {to_email}"}
        else:
            self.logger.error(f"Failed to send email: {response.status_code} - {response.text}")
            return {"success": False, "error": response.text}


# Global instances
customer_sessions = CustomerSessionStore()
_email_template_service: Optional[EmailTemplateService] = None


def get_email_template_service(webhook_base_url: str = None) -> EmailTemplateService:
    """Get or create the email template service singleton."""
    global _email_template_service
    
    if _email_template_service is None:
        from config import ElevenLabsConfig
        config = ElevenLabsConfig()
        
        if webhook_base_url is None:
            webhook_base_url = "http://localhost:8000/api/v1"
        
        _email_template_service = EmailTemplateService(config, webhook_base_url)
    
    return _email_template_service


def set_webhook_base_url(webhook_base_url: str) -> None:
    """Set the webhook base URL for the service."""
    global _email_template_service
    
    from config import ElevenLabsConfig
    config = ElevenLabsConfig()
    _email_template_service = EmailTemplateService(config, webhook_base_url)
