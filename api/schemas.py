"""
Pydantic schemas for request/response validation.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


# =============================================================================
# Common Schemas
# =============================================================================

class SuccessResponse(BaseModel):
    """Generic success response."""
    success: bool = True
    message: str = "Operation completed successfully"


class ErrorResponse(BaseModel):
    """Error response schema."""
    success: bool = False
    error: str
    detail: Optional[str] = None


class PaginationParams(BaseModel):
    """Pagination parameters."""
    cursor: Optional[str] = None
    page_size: int = Field(default=30, ge=1, le=100)


# =============================================================================
# Agent Schemas
# =============================================================================

class AgentPrompt(BaseModel):
    """Agent prompt configuration."""
    prompt: str


class AgentConfig(BaseModel):
    """Agent configuration."""
    first_message: Optional[str] = None
    language: str = "en"
    prompt: Optional[AgentPrompt] = None


class TTSConfig(BaseModel):
    """Text-to-speech configuration."""
    voice_id: Optional[str] = None


class ConversationConfig(BaseModel):
    """Full conversation configuration."""
    agent: Optional[AgentConfig] = None
    tts: Optional[TTSConfig] = None


class CreateAgentRequest(BaseModel):
    """Request schema for creating an agent."""
    name: Optional[str] = Field(None, description="Agent name")
    voice_id: Optional[str] = Field(None, description="Voice ID for TTS")
    first_message: Optional[str] = Field(None, description="Initial greeting message")
    system_prompt: Optional[str] = Field(None, description="System prompt for agent behavior")
    language: str = Field(default="en", description="Agent language")
    conversation_config: Optional[ConversationConfig] = Field(
        None, 
        description="Full conversation config (overrides other fields if provided)"
    )
    tool_ids: Optional[List[str]] = Field(
        None,
        description="List of tool IDs to enable for this agent"
    )
    knowledge_base_ids: Optional[List[str]] = Field(
        None,
        description="List of knowledge base document IDs to enable for this agent"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Customer Support Bot",
                "voice_id": "21m00Tcm4TlvDq8ikWAM",
                "first_message": "Hello! How can I help you today?",
                "system_prompt": "You are a helpful customer support agent.",
                "language": "en",
                "tool_ids": ["tool_abc123", "tool_xyz789"],
                "knowledge_base_ids": ["doc_abc123", "doc_xyz789"]
            }
        }


class CreateAgentResponse(BaseModel):
    """Response schema for agent creation."""
    agent_id: str


class AgentResponse(BaseModel):
    """Agent details response."""
    agent_id: str
    name: Optional[str] = None
    conversation_config: Optional[Dict[str, Any]] = None
    
    class Config:
        extra = "allow"


class AgentListResponse(BaseModel):
    """List of agents response."""
    agents: List[Dict[str, Any]]
    cursor: Optional[str] = None


class UpdateAgentRequest(BaseModel):
    """Request schema for updating an agent."""
    name: Optional[str] = None
    conversation_config: Optional[ConversationConfig] = None
    
    class Config:
        extra = "allow"


# =============================================================================
# Phone Number Schemas
# =============================================================================

class ImportPhoneNumberRequest(BaseModel):
    """Request schema for importing a phone number from Twilio."""
    phone_number: str = Field(..., description="Phone number in E.164 format")
    label: str = Field(..., description="Label for the phone number")
    sid: str = Field(..., description="Provider SID (Twilio Account SID)")
    token: str = Field(..., description="Provider authentication token")
    
    class Config:
        json_schema_extra = {
            "example": {
                "phone_number": "+14155551234",
                "label": "Customer Support Line",
                "sid": "ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
                "token": "your_auth_token"
            }
        }


class SIPTrunkCredentials(BaseModel):
    """SIP trunk credentials for digest authentication."""
    username: str = Field(..., description="SIP trunk username")
    password: Optional[str] = Field(None, description="SIP trunk password")
    
    class Config:
        extra = "allow"


class SIPTrunkConfig(BaseModel):
    """SIP trunk inbound/outbound configuration."""
    address: str = Field(..., description="Hostname or IP the SIP INVITE is sent to")
    transport: Optional[str] = Field(None, description="Transport protocol: auto, udp, tcp, tls")
    media_encryption: Optional[str] = Field(None, description="Media encryption: disabled, allowed, required")
    headers: Optional[Dict[str, str]] = Field(None, description="SIP X-* headers for INVITE request")
    credentials: Optional[SIPTrunkCredentials] = Field(None, description="Digest authentication credentials")
    
    class Config:
        extra = "allow"


class ImportSIPTrunkPhoneNumberRequest(BaseModel):
    """Request schema for importing a phone number from SIP trunk provider."""
    phone_number: str = Field(..., description="Phone number in E.164 format")
    label: str = Field(..., description="Label for the phone number")
    provider: str = Field("sip_trunk", description="Provider type (must be 'sip_trunk')")
    supports_inbound: bool = Field(True, description="Whether this phone number supports inbound calls")
    supports_outbound: bool = Field(True, description="Whether this phone number supports outbound calls")
    inbound_trunk_config: Optional[SIPTrunkConfig] = Field(None, description="Inbound SIP trunk configuration")
    outbound_trunk_config: Optional[SIPTrunkConfig] = Field(None, description="Outbound SIP trunk configuration")
    
    class Config:
        json_schema_extra = {
            "example": {
                "phone_number": "+390620199287",
                "label": "Italy SIP Line",
                "provider": "sip_trunk",
                "supports_inbound": True,
                "supports_outbound": True,
                "outbound_trunk_config": {
                    "address": "voiceagent.fibrapro.it",
                    "transport": "auto",
                    "media_encryption": "allowed",
                    "credentials": {
                        "username": "+390620199287",
                        "password": "your_password"
                    }
                },
                "inbound_trunk_config": {
                    "address": "sip.rtc.elevenlabs.io:5060",
                    "credentials": {
                        "username": "+390620199287",
                        "password": "your_password"
                    }
                }
            }
        }


class ImportPhoneNumberResponse(BaseModel):
    """Response for phone number import."""
    phone_number_id: str


class UpdatePhoneNumberRequest(BaseModel):
    """Request for updating a phone number."""
    agent_id: Optional[str] = None
    label: Optional[str] = None
    
    class Config:
        extra = "allow"


class PhoneNumberResponse(BaseModel):
    """Phone number details response."""
    phone_number_id: str
    phone_number: Optional[str] = None
    label: Optional[str] = None
    agent_id: Optional[str] = None
    
    class Config:
        extra = "allow"


class PhoneNumberListResponse(BaseModel):
    """List of phone numbers response."""
    phone_numbers: List[Dict[str, Any]]
    cursor: Optional[str] = None


# =============================================================================
# SIP Trunk Schemas
# =============================================================================

class CustomerInfoForCall(BaseModel):
    """Customer information for email tool context."""
    name: str = Field(..., description="Customer name")
    email: str = Field(..., description="Customer email address")
    
    class Config:
        extra = "allow"  # Allow additional fields


class EmailSenderConfig(BaseModel):
    """Configuration for who is sending emails (the business/user starting the call)."""
    user_email: str = Field(..., description="Email of the person/business sending emails (used for x-user-email header)")
    
    class Config:
        extra = "allow"


class OutboundCallRequest(BaseModel):
    """Request schema for outbound call via SIP trunk."""
    agent_id: str = Field(..., description="Agent ID to handle the call")
    agent_phone_number_id: str = Field(..., description="Phone number ID for caller ID")
    to_number: str = Field(..., description="Destination phone number (E.164 format)")
    custom_llm_extra_body: Optional[Dict[str, Any]] = Field(
        None, 
        description="Extra data for custom LLM"
    )
    dynamic_variables: Optional[Dict[str, str]] = Field(
        None, 
        description="Variables to inject into conversation"
    )
    first_message: Optional[str] = Field(
        None, 
        description="Override default first message"
    )
    customer_info: Optional[CustomerInfoForCall] = Field(
        None,
        description="Customer info for email tools (name, email of the recipient)"
    )
    sender_email: Optional[str] = Field(
        None,
        description="Email of the person/business starting the call (used as x-user-email when sending emails)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "agent_id": "J3Pbu5gP6NNKBscdCdwB",
                "agent_phone_number_id": "ph_abc123",
                "to_number": "+14155559999",
                "dynamic_variables": {
                    "customer_name": "John Doe",
                    "order_id": "ORD-12345"
                },
                "customer_info": {
                    "name": "John Doe",
                    "email": "john@example.com"
                },
                "sender_email": "business@mycompany.com"
            }
        }


class OutboundCallResponse(BaseModel):
    """Response for outbound call initiation."""
    success: bool
    message: Optional[str] = None
    conversation_id: Optional[str] = None
    sip_call_id: Optional[str] = None


class EcommerceCredentials(BaseModel):
    """Ecommerce platform credentials for call context."""
    platform: str = Field(..., description="Platform name: woocommerce, shopify")
    base_url: str = Field(..., description="Store base URL")
    api_key: str = Field(..., description="API key / Consumer key")
    api_secret: Optional[str] = Field(None, description="API secret (for WooCommerce)")
    access_token: Optional[str] = Field(None, description="Access token (for Shopify)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "platform": "woocommerce",
                "base_url": "https://mystore.com",
                "api_key": "ck_xxxxx",
                "api_secret": "cs_xxxxx"
            }
        }


class TwilioOutboundCallRequest(BaseModel):
    """Request schema for outbound call via Twilio."""
    agent_id: str = Field(..., description="Agent ID to handle the call")
    agent_phone_number_id: str = Field(..., description="Twilio phone number ID for caller ID")
    to_number: str = Field(..., description="Destination phone number (E.164 format)")
    dynamic_variables: Optional[Dict[str, str]] = Field(
        None, 
        description="Variables to inject into conversation (e.g., customer_name)"
    )
    first_message: Optional[str] = Field(
        None, 
        description="Override default first message"
    )
    ecommerce_credentials: Optional[EcommerceCredentials] = Field(
        None,
        description="Ecommerce platform credentials for product/order lookups during call"
    )
    customer_info: Optional[CustomerInfoForCall] = Field(
        None,
        description="Customer info for email tools (name, email of recipient). Required if using email templates."
    )
    sender_email: Optional[str] = Field(
        None,
        description="Email of the person/business starting the call (used as x-user-email when sending emails)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "agent_id": "agent_abc123",
                "agent_phone_number_id": "phnum_xyz789",
                "to_number": "+14155551234",
                "dynamic_variables": {
                    "customer_name": "John Doe"
                },
                "ecommerce_credentials": {
                    "platform": "woocommerce",
                    "base_url": "https://mystore.com",
                    "api_key": "ck_xxxxx",
                    "api_secret": "cs_xxxxx"
                },
                "customer_info": {
                    "name": "John Doe",
                    "email": "john@example.com"
                },
                "sender_email": "business@mycompany.com"
            }
        }


class TwilioOutboundCallResponse(BaseModel):
    """Response for Twilio outbound call initiation."""
    success: bool
    message: Optional[str] = None
    conversation_id: Optional[str] = None
    call_sid: Optional[str] = Field(None, alias="callSid")
    ecommerce_enabled: bool = Field(False, description="Whether ecommerce tools are available")
    
    class Config:
        populate_by_name = True


class EcommerceProductsRequest(BaseModel):
    """Request to fetch products for a conversation."""
    conversation_id: str = Field(..., description="Conversation ID")
    limit: int = Field(5, ge=1, le=20, description="Number of products to fetch")


class EcommerceOrdersRequest(BaseModel):
    """Request to fetch orders for a conversation."""
    conversation_id: str = Field(..., description="Conversation ID")
    limit: int = Field(5, ge=1, le=20, description="Number of orders to fetch")


class EcommerceProductsResponse(BaseModel):
    """Response with products data."""
    success: bool
    products: List[Dict[str, Any]] = []
    formatted: Optional[str] = None
    count: int = 0
    error: Optional[str] = None


class EcommerceOrdersResponse(BaseModel):
    """Response with orders data."""
    success: bool
    orders: List[Dict[str, Any]] = []
    formatted: Optional[str] = None
    count: int = 0
    error: Optional[str] = None


class CreateSIPTrunkRequest(BaseModel):
    """Request for creating a SIP trunk."""
    name: str = Field(..., description="SIP trunk name")
    sip_uri: str = Field(..., description="SIP URI")
    authentication: Optional[Dict[str, str]] = Field(
        None, 
        description="Authentication credentials"
    )
    
    class Config:
        extra = "allow"


class SIPTrunkResponse(BaseModel):
    """SIP trunk details response."""
    sip_trunk_id: str
    name: Optional[str] = None
    sip_uri: Optional[str] = None
    
    class Config:
        extra = "allow"


class SIPTrunkListResponse(BaseModel):
    """List of SIP trunks response."""
    sip_trunks: List[Dict[str, Any]]


# =============================================================================
# Batch Calling Schemas
# =============================================================================

class BatchRecipient(BaseModel):
    """Single recipient in a batch call."""
    phone_number: str = Field(..., description="Destination phone number")
    name: Optional[str] = Field(None, description="Recipient name")
    email: Optional[str] = Field(None, description="Recipient email (for email templates)")
    dynamic_variables: Optional[Dict[str, str]] = Field(
        None, 
        description="Call-specific variables"
    )
    
    class Config:
        extra = "allow"


class SubmitBatchJobRequest(BaseModel):
    """Request for submitting a batch calling job."""
    call_name: str = Field(..., description="Campaign/job name")
    agent_id: str = Field(..., description="Agent ID to handle calls")
    phone_number_id: str = Field(..., description="Phone number ID for caller ID (required for outbound calls)")
    recipients: List[BatchRecipient] = Field(..., description="List of recipients")
    scheduled_time_unix: Optional[int] = Field(None, description="Unix timestamp for scheduling")
    timezone: Optional[str] = Field(None, description="Timezone for scheduling")
    retry_count: int = Field(default=0, ge=0, le=5, description="Retry attempts for failed calls")
    ecommerce_credentials: Optional[EcommerceCredentials] = Field(
        None,
        description="E-commerce credentials for product/order lookups during calls (applies to all calls in batch)"
    )
    sender_email: Optional[str] = Field(
        None,
        description="Email of the sender/business (used as x-user-email when sending emails)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "call_name": "Q1 Customer Outreach",
                "agent_id": "J3Pbu5gP6NNKBscdCdwB",
                "phone_number_id": "phnum_abc123xyz",
                "recipients": [
                    {
                        "phone_number": "+14155551234",
                        "name": "John Doe",
                        "email": "john@example.com",
                        "dynamic_variables": {"appointment": "Feb 1, 2026"}
                    },
                    {
                        "phone_number": "+14155555678",
                        "name": "Jane Smith",
                        "email": "jane@example.com",
                        "dynamic_variables": {"appointment": "Feb 2, 2026"}
                    }
                ],
                "retry_count": 2,
                "ecommerce_credentials": {
                    "platform": "woocommerce",
                    "base_url": "https://mystore.com",
                    "api_key": "ck_xxxxx",
                    "api_secret": "cs_xxxxx"
                },
                "sender_email": "support@mycompany.com"
            }
        }


class BatchJobResponse(BaseModel):
    """Batch job details response."""
    id: str
    name: Optional[str] = None
    agent_id: Optional[str] = None
    status: Optional[str] = None
    phone_number_id: Optional[str] = None
    phone_provider: Optional[str] = None
    created_at_unix: Optional[int] = None
    scheduled_time_unix: Optional[int] = None
    timezone: Optional[str] = None
    total_calls_dispatched: int = 0
    total_calls_scheduled: int = 0
    total_calls_finished: int = 0
    last_updated_at_unix: Optional[int] = None
    retry_count: int = 0
    agent_name: Optional[str] = None
    
    class Config:
        extra = "allow"


class BatchJobListResponse(BaseModel):
    """List of batch jobs response."""
    jobs: List[Dict[str, Any]]
    cursor: Optional[str] = None


class BatchCallResult(BaseModel):
    """Individual call result from batch job."""
    to_number: Optional[str] = None
    status: Optional[str] = None
    conversation_id: Optional[str] = None
    
    class Config:
        extra = "allow"


class BatchJobCallsResponse(BaseModel):
    """List of calls from a batch job."""
    calls: List[Dict[str, Any]]
    cursor: Optional[str] = None


# =============================================================================
# Conversation Schemas
# =============================================================================

class TranscriptEntry(BaseModel):
    """Single transcript entry."""
    role: str = Field(..., description="Speaker role (agent or user)")
    message: str = Field(..., description="Message content")
    timestamp: Optional[float] = Field(None, description="Timestamp in seconds")
    
    class Config:
        extra = "allow"


class ConversationResponse(BaseModel):
    """Conversation details response."""
    conversation_id: str
    agent_id: Optional[str] = None
    status: Optional[str] = None
    transcript: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None
    call_duration_secs: Optional[float] = None
    start_time_unix: Optional[int] = None
    end_time_unix: Optional[int] = None
    
    class Config:
        extra = "allow"


class ConversationListResponse(BaseModel):
    """List of conversations response."""
    conversations: List[Dict[str, Any]]
    cursor: Optional[str] = None


# =============================================================================
# Knowledge Base Schemas
# =============================================================================

class KnowledgeBaseDocumentResponse(BaseModel):
    """Knowledge base document response."""
    document_id: str
    name: Optional[str] = None
    folder_path: Optional[Any] = None  # Can be string or list
    source_type: Optional[str] = None
    
    class Config:
        extra = "allow"


class KnowledgeBaseListResponse(BaseModel):
    """List of knowledge base documents."""
    documents: List[Dict[str, Any]]
    cursor: Optional[str] = None


class IngestTextRequest(BaseModel):
    """Request to ingest text content."""
    text: str = Field(..., description="Text content to ingest")
    name: Optional[str] = Field(None, description="Custom document name")
    parent_folder_id: Optional[str] = Field(None, description="Folder to place document in")


class IngestURLRequest(BaseModel):
    """Request to ingest content from URL."""
    url: str = Field(..., description="URL to scrape and ingest")
    name: Optional[str] = Field(None, description="Custom document name")
    parent_folder_id: Optional[str] = Field(None, description="Folder to place document in")


# =============================================================================
# Health Check
# =============================================================================

class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    api_accessible: bool
    version: str = "1.0.0"


# =============================================================================
# Email Templates
# =============================================================================

class EmailTemplateParameter(BaseModel):
    """Parameter definition for email template."""
    name: str = Field(..., description="Parameter name (e.g., 'date', 'time')")
    description: str = Field(..., description="Description of the parameter")
    required: bool = Field(default=True, description="Whether parameter is required")


class CreateEmailTemplateRequest(BaseModel):
    """Request to create an email template."""
    name: str = Field(..., description="Template name (e.g., 'confirm_appointment')")
    description: str = Field(..., description="Description for when AI should use this tool")
    subject_template: str = Field(..., description="Email subject with placeholders like {{date}}")
    body_template: str = Field(..., description="Email body with placeholders like {{customer_name}}")
    parameters: Optional[List[EmailTemplateParameter]] = Field(
        None, 
        description="Parameter definitions. If not provided, auto-extracted from templates"
    )
    webhook_base_url: Optional[str] = Field(
        None,
        description="Base URL for webhook (e.g., https://your-ngrok.ngrok-free.app/api/v1)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "confirm_appointment",
                "description": "Use this when the customer confirms an appointment booking",
                "subject_template": "Appointment Confirmed for {{date}} at {{time}}",
                "body_template": "Dear {{customer_name}},\n\nYour appointment has been confirmed.\n\nDate: {{date}}\nTime: {{time}}\nNotes: {{notes}}\n\nBest regards,\nAistein Team",
                "parameters": [
                    {"name": "date", "description": "Appointment date", "required": True},
                    {"name": "time", "description": "Appointment time", "required": True},
                    {"name": "notes", "description": "Additional notes", "required": False}
                ],
                "webhook_base_url": "https://your-ngrok.ngrok-free.app/api/v1"
            }
        }


class EmailTemplateResponse(BaseModel):
    """Response for email template operations."""
    template_id: str
    name: str
    description: str
    subject_template: str
    body_template: str
    parameters: List[EmailTemplateParameter]
    tool_id: Optional[str] = None
    created_at: str


class EmailTemplateListResponse(BaseModel):
    """Response for listing email templates."""
    templates: List[EmailTemplateResponse]
    count: int


class CustomerInfo(BaseModel):
    """Customer information for campaign context."""
    name: str = Field(..., description="Customer name")
    email: str = Field(..., description="Customer email address")
    phone: Optional[str] = Field(None, description="Customer phone number")
    
    class Config:
        extra = "allow"  # Allow additional fields


class StoreCustomerSessionRequest(BaseModel):
    """Request to store customer session info."""
    conversation_id: str = Field(..., description="Conversation/session ID")
    customer_info: CustomerInfo = Field(..., description="Customer information")


class SendEmailWebhookRequest(BaseModel):
    """Request body for email webhook (from ElevenLabs tool call)."""
    conversation_id: Optional[str] = Field(None, description="Conversation ID")
    
    class Config:
        extra = "allow"  # Allow dynamic parameters from template
