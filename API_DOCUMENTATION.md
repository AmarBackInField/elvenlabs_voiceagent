# ElevenLabs Agent API Documentation

> **Base URL:** `https://your-domain.com/api/v1` (or ngrok URL during development)
>
> **Version:** 1.0.0

---

## Table of Contents

1. [Getting Started](#1-getting-started)
2. [User Flow Overview](#2-user-flow-overview)
3. [Step 1: E-Commerce Tools (Predefined)](#3-step-1-e-commerce-tools-predefined)
4. [Step 2: Knowledge Base](#4-step-2-knowledge-base)
5. [Step 3: Email Templates](#5-step-3-email-templates)
6. [Step 4: Agent Creation](#6-step-4-agent-creation)
7. [Step 5: Agent Update](#7-step-5-agent-update)
8. [Step 6: Phone Number Setup (Twilio/SIP)](#8-step-6-phone-number-setup-twiliosip)
9. [Step 7: Making Calls](#9-step-7-making-calls)
10. [Step 8: Running Campaigns (Batch Calling)](#10-step-8-running-campaigns-batch-calling)
11. [Webhooks (Internal)](#11-webhooks-internal)
12. [Error Handling](#12-error-handling)

---

## 1. Getting Started

### Prerequisites

1. **ElevenLabs API Key**: Set in environment variable `ELEVENLABS_API_KEY`
2. **Twilio Account** (for phone calls): Account SID and Auth Token
3. **ngrok** (for development): To expose local webhooks to ElevenLabs

### Environment Setup

```bash
# Required
export ELEVENLABS_API_KEY=your_api_key_here

# Optional - for email sending
export EMAIL_API_URL=https://your-email-api.com/email/send
```

### Start the Server

```bash
# Development with ngrok
python api/main.py  # Runs on port 8000
ngrok http 8000     # Get public URL
```

### Health Check

```
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "api_accessible": true,
  "version": "1.0.0"
}
```

---

## 2. User Flow Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         SETUP PHASE                                      │
├─────────────────────────────────────────────────────────────────────────┤
│  1. Create E-Commerce Tools (optional) ──► Get tool_ids                 │
│  2. Create Knowledge Base Documents ─────► Get document_ids             │
│  3. Create Email Templates ──────────────► Get tool_ids for emails      │
│  4. Create Agent with tools & knowledge ─► Get agent_id                 │
│  5. Update Agent (if needed) ────────────► Modified agent               │
├─────────────────────────────────────────────────────────────────────────┤
│                       PHONE SETUP                                        │
├─────────────────────────────────────────────────────────────────────────┤
│  6. Import Phone Number (Twilio/SIP) ────► Get phone_number_id          │
│  7. Assign Agent to Phone Number ────────► Ready for calls              │
├─────────────────────────────────────────────────────────────────────────┤
│                       CALLING PHASE                                      │
├─────────────────────────────────────────────────────────────────────────┤
│  8. Single Call (Twilio or SIP) ─────────► conversation_id              │
│  9. Batch Campaign ──────────────────────► job_id + multiple calls      │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Step 1: E-Commerce Tools (Predefined)

E-commerce tools allow your agent to fetch products and orders from WooCommerce or Shopify during calls.

### 3.1 Create E-Commerce Tools

Creates both `get_products` and `get_orders` tools in one request.

```
POST /api/v1/tools/ecommerce
```

**Request Body:**
```json
{
  "webhook_base_url": "https://your-ngrok-url.ngrok-free.dev/api/v1"
}
```

**Response:**
```json
{
  "products_tool_id": "tool_abc123xyz",
  "orders_tool_id": "tool_def456uvw"
}
```

> **Important:** Save these `tool_id` values. You'll need them when creating agents.

### 3.2 Create Custom Webhook Tool

For custom integrations beyond e-commerce.

```
POST /api/v1/tools/webhook
```

**Request Body:**
```json
{
  "name": "check_inventory",
  "description": "Check product inventory. Use when user asks about stock availability.",
  "webhook_url": "https://your-api.com/api/v1/webhook/inventory",
  "http_method": "POST",
  "parameters": [
    {
      "name": "product_id",
      "type": "string",
      "description": "The product ID to check",
      "required": true
    },
    {
      "name": "location",
      "type": "string",
      "description": "Warehouse location",
      "required": false
    }
  ]
}
```

**Response:**
```json
{
  "tool_id": "tool_custom123",
  "name": "check_inventory",
  "description": "Check product inventory...",
  "type": "webhook"
}
```

### 3.3 List All Tools

```
GET /api/v1/tools?page_size=30&cursor=optional_cursor
```

**Response:**
```json
{
  "tools": [
    {
      "tool_id": "tool_abc123",
      "name": "get_products",
      "type": "webhook"
    },
    {
      "tool_id": "tool_def456",
      "name": "get_orders",
      "type": "webhook"
    }
  ],
  "cursor": "next_page_cursor_or_null"
}
```

### 3.4 Get Tool Details

```
GET /api/v1/tools/{tool_id}
```

### 3.5 Delete Tool

```
DELETE /api/v1/tools/{tool_id}
```

**Response:**
```json
{
  "success": true,
  "message": "Tool tool_abc123 deleted successfully"
}
```

---

## 4. Step 2: Knowledge Base

Knowledge base documents give your agent access to company information, FAQs, product details, etc.

### 4.1 Create Document from Text

```
POST /api/v1/knowledge-base/text
```

**Request Body:**
```json
{
  "text": "Company FAQ:\n\nQ: What are your business hours?\nA: We are open Monday-Friday, 9 AM to 6 PM EST.\n\nQ: What is your return policy?\nA: 30-day money-back guarantee on all products.",
  "name": "Company FAQ",
  "parent_folder_id": null
}
```

**Response:**
```json
{
  "document_id": "KBDoc_abc123xyz",
  "id": "KBDoc_abc123xyz",
  "name": "Company FAQ",
  "folder_path": null,
  "source_type": "text",
  "status": "processing"
}
```

> **Note:** Use the `document_id` (or `id`) value when attaching to agents via `knowledge_base_ids`.

### 4.2 Create Document from URL

Scrapes content from a webpage.

```
POST /api/v1/knowledge-base/url
```

**Request Body:**
```json
{
  "url": "https://yourcompany.com/about-us",
  "name": "About Us Page",
  "parent_folder_id": null
}
```

**Response:**
```json
{
  "document_id": "KBDoc_def456uvw",
  "id": "KBDoc_def456uvw",
  "name": "About Us Page",
  "folder_path": null,
  "source_type": "url",
  "status": "processing"
}
```

### 4.3 Create Document from File Upload

Supports: PDF, TXT, MD, DOCX

```
POST /api/v1/knowledge-base/file
Content-Type: multipart/form-data
```

**Form Fields:**
- `file`: The file to upload (required)
- `name`: Custom document name (optional)
- `parent_folder_id`: Folder ID (optional)

**cURL Example:**
```bash
curl -X POST "https://your-api.com/api/v1/knowledge-base/file" \
  -F "file=@product_catalog.pdf" \
  -F "name=Product Catalog 2026"
```

**Response:**
```json
{
  "document_id": "KBDoc_ghi789rst",
  "id": "KBDoc_ghi789rst",
  "name": "Product Catalog 2026",
  "folder_path": null,
  "source_type": "file",
  "status": "processing"
}
```

### 4.4 Unified Ingest Endpoint

Single endpoint for all ingestion types.

```
POST /api/v1/knowledge-base/ingest
Content-Type: multipart/form-data
```

**Form Fields:**
- `source_type`: `text`, `url`, or `file` (required)
- `text`: Content if source_type=text
- `url`: URL if source_type=url
- `file`: File if source_type=file
- `name`: Custom name (optional)
- `parent_folder_id`: Folder ID (optional)

### 4.5 List All Documents

```
GET /api/v1/knowledge-base?page_size=30&cursor=optional
```

**Response:**
```json
{
  "documents": [
    {
      "id": "KBDoc_abc123xyz",
      "name": "Company FAQ",
      "type": "file",
      "status": "ready",
      "created_at_unix": 1738310400
    },
    {
      "id": "KBDoc_def456uvw",
      "name": "About Us Page",
      "type": "file",
      "status": "ready",
      "created_at_unix": 1738310500
    }
  ],
  "cursor": null
}
```

### 4.6 Get Document Details

```
GET /api/v1/knowledge-base/{document_id}
```

**Response:**
```json
{
  "document_id": "KBDoc_abc123xyz",
  "id": "KBDoc_abc123xyz",
  "name": "Company FAQ",
  "type": "file",
  "status": "ready",
  "created_at_unix": 1738310400
}
```

### 4.7 Delete Document

```
DELETE /api/v1/knowledge-base/{document_id}
```

**Response:**
```json
{
  "success": true,
  "message": "Document KBDoc_abc123xyz deleted successfully"
}
```

> **Important:** Save the `id` or `document_id` values. You'll need them when creating agents via `knowledge_base_ids`.

---

## 5. Step 3: Email Templates

Email templates allow your agent to send emails during calls (e.g., appointment confirmations, receipts).

### 5.1 Create Email Template

Creating a template also creates a corresponding webhook tool in ElevenLabs.

```
POST /api/v1/email-templates
```

**Request Body:**
```json
{
  "name": "confirm_appointment",
  "description": "Use this tool when the customer confirms their appointment. This will send them a confirmation email with the appointment details.",
  "subject_template": "Appointment Confirmed - {{date}} at {{time}}",
  "body_template": "Dear {{customer_name}},\n\nYour appointment has been confirmed for:\n\nDate: {{date}}\nTime: {{time}}\n\n{{notes}}\n\nIf you need to reschedule or cancel, please contact us.\n\nThank you!",
  "parameters": [
    {
      "name": "date",
      "description": "The appointment date (e.g., January 30, 2026)",
      "required": true
    },
    {
      "name": "time",
      "description": "The appointment time (e.g., 2:00 PM)",
      "required": true
    },
    {
      "name": "notes",
      "description": "Any additional notes about the appointment",
      "required": false
    }
  ],
  "webhook_base_url": "https://your-ngrok-url.ngrok-free.dev/api/v1"
}
```

**Response:**
```json
{
  "template_id": "confirm_appointment",
  "name": "confirm_appointment",
  "description": "Use this tool when the customer confirms their appointment...",
  "subject_template": "Appointment Confirmed - {{date}} at {{time}}",
  "body_template": "Dear {{customer_name}}...",
  "parameters": [
    {"name": "date", "description": "The appointment date...", "required": true},
    {"name": "time", "description": "The appointment time...", "required": true},
    {"name": "notes", "description": "Any additional notes...", "required": false}
  ],
  "tool_id": "tool_email_abc123",
  "created_at": "2026-01-28T08:38:02.753538"
}
```

### Template Placeholders

| Placeholder | Source | Description |
|-------------|--------|-------------|
| `{{customer_name}}` | Session | Auto-filled from customer info |
| `{{customer_email}}` | Session | Auto-filled from customer info |
| `{{name}}` | Session | Alias for customer_name |
| `{{email}}` | Session | Alias for customer_email |
| `{{date}}`, `{{time}}`, etc. | AI | Provided by the agent during call |

> **Important:** The `tool_id` is automatically created. Add this to your agent's `tool_ids` array.

### 5.2 List Email Templates

```
GET /api/v1/email-templates
```

**Response:**
```json
{
  "templates": [
    {
      "template_id": "confirm_appointment",
      "name": "confirm_appointment",
      "tool_id": "tool_email_abc123",
      "created_at": "2026-01-28T08:38:02.753538"
    }
  ],
  "count": 1
}
```

### 5.3 Get Template Details

```
GET /api/v1/email-templates/{template_id}
```

### 5.4 Delete Template

Also deletes the associated ElevenLabs tool.

```
DELETE /api/v1/email-templates/{template_id}
```

### 5.5 Customer Session Management

Customer sessions store recipient info for email personalization.

#### Store Customer Session

```
POST /api/v1/email-templates/sessions
```

**Request Body:**
```json
{
  "conversation_id": "conv_abc123",
  "customer_info": {
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+14155551234"
  }
}
```

> **Note:** Customer sessions are automatically created when making outbound calls with `customer_info`.

#### Get Customer Session

```
GET /api/v1/email-templates/sessions/{conversation_id}
```

#### List All Sessions (Debug)

```
GET /api/v1/email-templates/sessions
```

#### Delete Session

```
DELETE /api/v1/email-templates/sessions/{conversation_id}
```

---

## 6. Step 4: Agent Creation

Create an AI agent with tools and knowledge base attached.

### 6.1 Create Agent (Simple)

```
POST /api/v1/agents
```

**Request Body:**
```json
{
  "name": "Customer Support Agent",
  "language": "en",
  "voice_id": "21m00Tcm4TlvDq8ikWAM",
  "first_message": "Hello! This is Sarah from Acme Corp. How can I help you today?",
  "system_prompt": "You are Sarah, a friendly and professional customer support agent for Acme Corp.\n\nYour responsibilities:\n1. Answer customer questions about products and services\n2. Help schedule and confirm appointments\n3. Provide order status updates\n\nWhen a customer confirms an appointment:\n- Get the date and time\n- Use the confirm_appointment tool to send confirmation email\n\nBe concise, polite, and helpful. Always verify details before taking actions.",
  "tool_ids": [
    "tool_products_abc123",
    "tool_orders_def456",
    "tool_email_xyz789"
  ],
  "knowledge_base_ids": [
    "doc_faq123",
    "doc_about456"
  ]
}
```

**Response:**
```json
{
  "agent_id": "agent_abc123xyz"
}
```

### 6.2 Create Agent (Full Config)

For advanced configuration including TTS settings.

```
POST /api/v1/agents
```

**Request Body:**
```json
{
  "name": "Italian Support Agent",
  "conversation_config": {
    "agent": {
      "first_message": "Ciao! Come posso aiutarti oggi?",
      "language": "it",
      "prompt": {
        "prompt": "Sei un assistente cliente professionale..."
      }
    },
    "tts": {
      "voice_id": "italian_voice_id"
    }
  },
  "tool_ids": ["tool_abc123"],
  "knowledge_base_ids": ["doc_xyz789"]
}
```

### 6.3 List Agents

```
GET /api/v1/agents?page_size=30&cursor=optional
```

**Response:**
```json
{
  "agents": [
    {
      "agent_id": "agent_abc123",
      "name": "Customer Support Agent",
      "conversation_config": {
        "agent": {
          "language": "en",
          "first_message": "Hello!..."
        }
      }
    }
  ],
  "cursor": null
}
```

### 6.4 Get Agent Details

```
GET /api/v1/agents/{agent_id}
```

**Response:**
```json
{
  "agent_id": "agent_abc123",
  "name": "Customer Support Agent",
  "conversation_config": {
    "agent": {
      "first_message": "Hello! This is Sarah...",
      "language": "en",
      "prompt": {
        "prompt": "You are Sarah...",
        "tool_ids": ["tool_abc", "tool_def"],
        "knowledge_base": [
          {"id": "doc_faq123", "type": "file", "name": "FAQ"}
        ]
      }
    },
    "tts": {
      "voice_id": "21m00Tcm4TlvDq8ikWAM",
      "model_id": "eleven_turbo_v2_5"
    }
  }
}
```

### 6.5 Delete Agent

```
DELETE /api/v1/agents/{agent_id}
```

---

## 7. Step 5: Agent Update

### 7.1 Update Agent (Full)

```
PATCH /api/v1/agents/{agent_id}
```

**Request Body:**
```json
{
  "name": "Updated Agent Name",
  "conversation_config": {
    "agent": {
      "first_message": "New greeting message",
      "language": "en"
    }
  }
}
```

### 7.2 Update Agent Prompt (Simplified)

Quick endpoint to update prompt-related settings only.

```
PATCH /api/v1/agents/{agent_id}/prompt
```

**Request Body:**
```json
{
  "first_message": "Hello! Thank you for calling Acme Corp. How may I assist you?",
  "language": "en",
  "system_prompt": "You are an updated customer support agent...",
  "tool_ids": [
    "tool_products_abc",
    "tool_orders_def",
    "tool_new_feature_xyz"
  ],
  "knowledge_base_ids": [
    "doc_faq123",
    "doc_new_policies_456"
  ]
}
```

**Response:**
```json
{
  "agent_id": "agent_abc123",
  "name": "Customer Support Agent",
  "conversation_config": {
    "agent": {
      "first_message": "Hello! Thank you for calling...",
      "language": "en",
      "prompt": {
        "prompt": "You are an updated customer support agent...",
        "tool_ids": ["tool_products_abc", "tool_orders_def", "tool_new_feature_xyz"],
        "knowledge_base": [
          {"id": "doc_faq123", "type": "file", "name": "KB Document 1"},
          {"id": "doc_new_policies_456", "type": "file", "name": "KB Document 2"}
        ]
      }
    }
  }
}
```

> **Note:** Only provided fields are updated. Omit fields you don't want to change.

---

## 8. Step 6: Phone Number Setup (Twilio/SIP)

### 8.1 Import Phone Number from Twilio

```
POST /api/v1/phone-numbers
```

**Request Body:**
```json
{
  "phone_number": "+14155551234",
  "label": "Customer Support Line",
  "sid": "ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
  "token": "your_twilio_auth_token"
}
```

**Response:**
```json
{
  "phone_number_id": "phnum_abc123xyz"
}
```

### 8.2 Import Phone Number from SIP Trunk Provider

For non-Twilio SIP providers (Vonage, Fibrapro, etc.)

```
POST /api/v1/phone-numbers/sip-trunk
```

**Request Body:**
```json
{
  "phone_number": "+390620199287",
  "label": "Italy SIP Line",
  "provider": "sip_trunk",
  "supports_inbound": true,
  "supports_outbound": true,
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
```

**Response:**
```json
{
  "phone_number_id": "phnum_sip123xyz"
}
```

**SIP Trunk Configuration Fields:**

| Field | Description |
|-------|-------------|
| `phone_number` | Your SIP phone number in E.164 format |
| `label` | Display name for the number |
| `provider` | Must be `"sip_trunk"` |
| `supports_inbound` | Enable inbound calls (default: true) |
| `supports_outbound` | Enable outbound calls (default: true) |

**Trunk Config (outbound/inbound) Fields:**

| Field | Description | Required |
|-------|-------------|----------|
| `address` | Hostname or IP the SIP INVITE is sent to | Yes |
| `transport` | Protocol: `auto`, `udp`, `tcp`, `tls` | No |
| `media_encryption` | Encryption: `disabled`, `allowed`, `required` | No |
| `headers` | Custom SIP X-* headers (key-value map) | No |
| `credentials.username` | SIP digest auth username | No |
| `credentials.password` | SIP digest auth password | No |

> **Note:** The ElevenLabs inbound SIP endpoint is `sip.rtc.elevenlabs.io:5060`. Configure your SIP provider to route inbound calls to this endpoint.

### 8.3 List Phone Numbers

```
GET /api/v1/phone-numbers?page_size=30
```

**Response:**
```json
{
  "phone_numbers": [
    {
      "phone_number_id": "phnum_abc123",
      "phone_number": "+14155551234",
      "label": "Customer Support Line",
      "agent_id": null,
      "provider": "twilio"
    },
    {
      "phone_number_id": "phnum_sip456",
      "phone_number": "+390620199287",
      "label": "Italy SIP Line",
      "agent_id": null,
      "provider": "sip_trunk"
    }
  ],
  "cursor": null
}
```

### 8.4 Assign Agent to Phone Number

This enables the agent to handle incoming calls on this number.

```
PATCH /api/v1/phone-numbers/{phone_number_id}
```

**Request Body:**
```json
{
  "agent_id": "agent_abc123xyz",
  "label": "Support Line - English"
}
```

**Response:**
```json
{
  "phone_number_id": "phnum_abc123",
  "phone_number": "+14155551234",
  "label": "Support Line - English",
  "agent_id": "agent_abc123xyz"
}
```

### 8.5 Delete Phone Number

```
DELETE /api/v1/phone-numbers/{phone_number_id}
```

**Response:**
```json
{
  "success": true,
  "message": "Phone number phnum_abc123 deleted successfully"
}
```

---

### Phone Number Provider Comparison

| Provider | Import Endpoint | Required Fields |
|----------|----------------|-----------------|
| **Twilio** | `POST /phone-numbers` | `phone_number`, `label`, `sid`, `token` |
| **SIP Trunk** | `POST /phone-numbers/sip-trunk` | `phone_number`, `label`, `provider`, `outbound_trunk_config` |

> **Note:** Both Twilio and SIP trunk phone numbers can be used for outbound calls. Use the respective outbound call endpoint based on your provider.

---

## 9. Step 7: Making Calls

### 9.1 Outbound Call via Twilio

Use this for phone numbers imported from Twilio.

```
POST /api/v1/phone-numbers/twilio/outbound-call
```

**Request Body (Basic):**
```json
{
  "agent_id": "agent_abc123xyz",
  "agent_phone_number_id": "phnum_abc123",
  "to_number": "+14155559999"
}
```

**Request Body (Full - with E-commerce & Email):**
```json
{
  "agent_id": "agent_abc123xyz",
  "agent_phone_number_id": "phnum_abc123",
  "to_number": "+14155559999",
  "first_message": "Hello John! This is Sarah from Acme Corp calling about your appointment.",
  "dynamic_variables": {
    "customer_name": "John Doe",
    "appointment_date": "February 1, 2026"
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
  "sender_email": "support@acmecorp.com"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Call initiated",
  "conversation_id": "conv_abc123xyz",
  "call_sid": "CA1234567890abcdef",
  "ecommerce_enabled": true
}
```

### 9.2 Outbound Call via SIP Trunk

Use this for SIP trunk phone numbers.

```
POST /api/v1/sip-trunk/outbound-call
```

**Request Body:**
```json
{
  "agent_id": "agent_abc123xyz",
  "agent_phone_number_id": "phnum_sip123",
  "to_number": "+14155559999",
  "first_message": "Hello! This is your appointment reminder call.",
  "dynamic_variables": {
    "customer_name": "Jane Smith",
    "order_id": "ORD-12345"
  },
  "customer_info": {
    "name": "Jane Smith",
    "email": "jane@example.com"
  },
  "sender_email": "noreply@acmecorp.com"
}
```

**Response:**
```json
{
  "success": true,
  "message": "SIP call initiated",
  "conversation_id": "conv_sip123xyz",
  "sip_call_id": "sip-call-id-123"
}
```

### E-commerce Platform Credentials

| Platform | Required Fields |
|----------|----------------|
| **WooCommerce** | `platform`, `base_url`, `api_key`, `api_secret` |
| **Shopify** | `platform`, `base_url`, `api_key`, `access_token` |

**WooCommerce Example:**
```json
{
  "platform": "woocommerce",
  "base_url": "https://mystore.com",
  "api_key": "ck_xxxxxxxxxxxxxxx",
  "api_secret": "cs_xxxxxxxxxxxxxxx"
}
```

**Shopify Example:**
```json
{
  "platform": "shopify",
  "base_url": "https://mystore.myshopify.com",
  "api_key": "your_api_key",
  "access_token": "shpat_xxxxxxxxxxxxxxx"
}
```

---

## 10. Step 8: Running Campaigns (Batch Calling)

### 10.1 Submit Batch Calling Job

```
POST /api/v1/batch-calling/submit
```

**Request Body (Basic):**
```json
{
  "call_name": "Q1 Appointment Reminders",
  "agent_id": "agent_abc123xyz",
  "phone_number_id": "phnum_abc123",
  "recipients": [
    {
      "phone_number": "+14155551111",
      "name": "John Doe",
      "dynamic_variables": {
        "customer_name": "John",
        "appointment_date": "February 1, 2026"
      }
    },
    {
      "phone_number": "+14155552222",
      "name": "Jane Smith",
      "dynamic_variables": {
        "customer_name": "Jane",
        "appointment_date": "February 1, 2026"
      }
    }
  ],
  "retry_count": 2
}
```

**Request Body (Full - with E-commerce & Email Templates):**
```json
{
  "call_name": "Q1 Customer Outreach Campaign",
  "agent_id": "agent_abc123xyz",
  "phone_number_id": "phnum_abc123",
  "recipients": [
    {
      "phone_number": "+14155551111",
      "name": "John Doe",
      "email": "john@example.com",
      "dynamic_variables": {
        "customer_name": "John",
        "appointment_date": "February 1, 2026",
        "appointment_time": "10:00 AM"
      }
    },
    {
      "phone_number": "+14155552222",
      "name": "Jane Smith",
      "email": "jane@example.com",
      "dynamic_variables": {
        "customer_name": "Jane",
        "appointment_date": "February 1, 2026",
        "appointment_time": "2:00 PM"
      }
    },
    {
      "phone_number": "+14155553333",
      "name": "Bob Johnson",
      "email": "bob@example.com",
      "dynamic_variables": {
        "customer_name": "Bob",
        "appointment_date": "February 2, 2026",
        "appointment_time": "9:00 AM"
      }
    }
  ],
  "scheduled_time_unix": 1738400400,
  "timezone": "America/New_York",
  "retry_count": 2,
  "ecommerce_credentials": {
    "platform": "woocommerce",
    "base_url": "https://mystore.com",
    "api_key": "ck_xxxxx",
    "api_secret": "cs_xxxxx"
  },
  "sender_email": "support@mycompany.com"
}
```

**Response:**
```json
{
  "id": "batch_abc123xyz",
  "name": "Q1 Appointment Reminders",
  "agent_id": "agent_abc123xyz",
  "status": "pending",
  "phone_number_id": "phnum_abc123",
  "phone_provider": "twilio",
  "created_at_unix": 1738310400,
  "scheduled_time_unix": 1738400400,
  "timezone": "America/New_York",
  "total_calls_dispatched": 0,
  "total_calls_scheduled": 3,
  "total_calls_finished": 0,
  "retry_count": 2
}
```

### Batch Calling with E-commerce & Email Templates

To enable e-commerce lookups and email sending during batch calls:

1. **E-commerce**: Add `ecommerce_credentials` to the batch job request. All calls in the batch will have access to product/order lookups.

2. **Email Templates**: Include `email` field for each recipient. The agent can then send emails to customers during calls.

3. **Sender Email**: Set `sender_email` to specify the business email used as the sender.

### Recipient Object Structure

```json
{
  "phone_number": "+14155551234",  // Required, E.164 format
  "name": "Customer Name",         // Optional, for personalization
  "email": "customer@example.com", // Optional, required for email templates
  "dynamic_variables": {           // Optional, injected into conversation
    "custom_field_1": "value1",
    "custom_field_2": "value2"
  }
}
```

### Campaign Constraints & Limits

| Constraint | Limit | Description |
|------------|-------|-------------|
| **Max Recipients per Batch** | 1000 | Maximum recipients in single job |
| **Page Size** | 1-100 | Results per page for listing |
| **Retry Count** | 0-5 | Failed call retry attempts |
| **Phone Format** | E.164 | Must be +CountryCode format |
| **Concurrent Calls** | Platform limit | Depends on ElevenLabs plan |

### Recipient Object Structure

```json
{
  "phone_number": "+14155551234",  // Required, E.164 format
  "name": "Customer Name",         // Optional, for reference
  "dynamic_variables": {           // Optional, injected into conversation
    "custom_field_1": "value1",
    "custom_field_2": "value2"
  }
}
```

### 10.2 List Batch Jobs

```
GET /api/v1/batch-calling?status=running&page_size=30
```

**Query Parameters:**
- `status`: `pending`, `running`, `completed`, `failed` (optional)
- `cursor`: Pagination cursor (optional)
- `page_size`: 1-100 (default: 30)

**Response:**
```json
{
  "jobs": [
    {
      "id": "batch_abc123",
      "name": "Q1 Appointment Reminders",
      "status": "running",
      "total_calls_scheduled": 100,
      "total_calls_dispatched": 45,
      "total_calls_finished": 42
    }
  ],
  "cursor": "next_page_cursor"
}
```

### 10.3 Get Batch Job Status

```
GET /api/v1/batch-calling/{job_id}
```

**Response:**
```json
{
  "id": "batch_abc123xyz",
  "name": "Q1 Appointment Reminders",
  "agent_id": "agent_abc123xyz",
  "status": "running",
  "phone_number_id": "phnum_abc123",
  "phone_provider": "twilio",
  "created_at_unix": 1738310400,
  "scheduled_time_unix": 1738400400,
  "timezone": "America/New_York",
  "total_calls_dispatched": 85,
  "total_calls_scheduled": 100,
  "total_calls_finished": 80,
  "last_updated_at_unix": 1738402500,
  "retry_count": 2,
  "agent_name": "Customer Support Agent"
}
```

### Job Status Values

| Status | Description |
|--------|-------------|
| `pending` | Job created, waiting to start |
| `running` | Calls are being made |
| `completed` | All calls finished |
| `failed` | Job failed (check calls for details) |
| `cancelled` | Job was cancelled |

### 10.4 Get Individual Call Results

```
GET /api/v1/batch-calling/{job_id}/calls?status=completed&page_size=50
```

**Response:**
```json
{
  "calls": [
    {
      "to_number": "+14155551111",
      "status": "completed",
      "conversation_id": "conv_call1_abc",
      "duration_seconds": 145,
      "outcome": "appointment_confirmed"
    },
    {
      "to_number": "+14155552222",
      "status": "no_answer",
      "conversation_id": null,
      "retry_count": 1
    }
  ],
  "cursor": "next_page_cursor"
}
```

### Call Status Values

| Status | Description |
|--------|-------------|
| `scheduled` | Call is queued |
| `dialing` | Call is being placed |
| `in_progress` | Call is active |
| `completed` | Call finished successfully |
| `no_answer` | Recipient didn't answer |
| `busy` | Line was busy |
| `failed` | Call failed |
| `voicemail` | Reached voicemail |

### 10.5 Cancel Batch Job

Stops pending calls. In-progress calls will complete.

```
POST /api/v1/batch-calling/{job_id}/cancel
```

**Response:**
```json
{
  "success": true,
  "message": "Batch job batch_abc123 cancelled successfully"
}
```

---

## 11. Webhooks (Internal)

These endpoints are called by ElevenLabs agents during conversations. They are automatically configured when you create tools.

### 11.1 E-commerce Products Webhook

```
POST /api/v1/webhook/ecommerce/products
```

Called when agent uses `get_products` tool.

### 11.2 E-commerce Orders Webhook

```
POST /api/v1/webhook/ecommerce/orders
```

Called when agent uses `get_orders` tool.

### 11.3 Email Webhook

```
POST /api/v1/webhook/email/{template_id}
```

Called when agent uses email template tool.

**Example payload from ElevenLabs:**
```json
{
  "conversation_id": "conv_abc123",
  "date": "February 1, 2026",
  "time": "2:00 PM",
  "notes": "Please bring your ID"
}
```

### 11.4 Test Webhook

```
POST /api/v1/webhook/test
```

For testing webhook connectivity.

---

## 12. Error Handling

### Error Response Format

All errors follow this format:

```json
{
  "success": false,
  "error": "Error description",
  "detail": "Additional details (optional)"
}
```

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request (invalid parameters) |
| 401 | Authentication failed |
| 404 | Resource not found |
| 422 | Validation error |
| 429 | Rate limit exceeded |
| 500 | Internal server error |

### Common Errors

**Missing API Key:**
```json
{
  "success": false,
  "error": "Authentication failed",
  "detail": "ELEVENLABS_API_KEY environment variable not set"
}
```

**Agent Not Found:**
```json
{
  "success": false,
  "error": "Agent not found: agent_invalid123"
}
```

**Invalid Phone Number:**
```json
{
  "success": false,
  "error": "Invalid phone number format. Must be E.164 (e.g., +14155551234)"
}
```

**Rate Limited:**
```json
{
  "success": false,
  "error": "Rate limit exceeded",
  "detail": "Retry after 60 seconds"
}
```

---

## Quick Reference: Complete Flow Example

### 1. Create Tools

```bash
# Create e-commerce tools
curl -X POST "$BASE_URL/api/v1/tools/ecommerce" \
  -H "Content-Type: application/json" \
  -d '{"webhook_base_url": "https://your-ngrok.ngrok-free.dev/api/v1"}'
# Response: {"products_tool_id": "tool_prod123", "orders_tool_id": "tool_ord456"}
```

### 2. Create Knowledge Base

```bash
# Create FAQ document
curl -X POST "$BASE_URL/api/v1/knowledge-base/text" \
  -H "Content-Type: application/json" \
  -d '{"text": "FAQ content here...", "name": "Company FAQ"}'
# Response: {"document_id": "doc_faq789"}
```

### 3. Create Email Template

```bash
curl -X POST "$BASE_URL/api/v1/email-templates" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "confirm_appointment",
    "description": "Send appointment confirmation email",
    "subject_template": "Appointment Confirmed - {{date}}",
    "body_template": "Dear {{customer_name}},\n\nConfirmed for {{date}} at {{time}}.",
    "webhook_base_url": "https://your-ngrok.ngrok-free.dev/api/v1"
  }'
# Response: {"template_id": "confirm_appointment", "tool_id": "tool_email123"}
```

### 4. Create Agent

```bash
curl -X POST "$BASE_URL/api/v1/agents" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Support Agent",
    "language": "en",
    "first_message": "Hello! How can I help you?",
    "system_prompt": "You are a helpful support agent...",
    "tool_ids": ["tool_prod123", "tool_ord456", "tool_email123"],
    "knowledge_base_ids": ["doc_faq789"]
  }'
# Response: {"agent_id": "agent_main123"}
```

### 5. Import Phone Number

```bash
curl -X POST "$BASE_URL/api/v1/phone-numbers" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+14155551234",
    "label": "Support Line",
    "sid": "ACXXXXXXXX",
    "token": "your_token"
  }'
# Response: {"phone_number_id": "phnum_abc123"}
```

### 6. Assign Agent to Number

```bash
curl -X PATCH "$BASE_URL/api/v1/phone-numbers/phnum_abc123" \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "agent_main123"}'
```

### 7. Make a Test Call

```bash
curl -X POST "$BASE_URL/api/v1/phone-numbers/twilio/outbound-call" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "agent_main123",
    "agent_phone_number_id": "phnum_abc123",
    "to_number": "+14155559999",
    "customer_info": {"name": "John Doe", "email": "john@example.com"},
    "sender_email": "support@company.com"
  }'
# Response: {"success": true, "conversation_id": "conv_test123"}
```

### 8. Run Campaign

```bash
curl -X POST "$BASE_URL/api/v1/batch-calling/submit" \
  -H "Content-Type: application/json" \
  -d '{
    "call_name": "January Campaign",
    "agent_id": "agent_main123",
    "phone_number_id": "phnum_abc123",
    "recipients": [
      {"phone_number": "+14155551111", "name": "Customer 1"},
      {"phone_number": "+14155552222", "name": "Customer 2"}
    ],
    "retry_count": 2
  }'
# Response: {"id": "batch_jan123", "status": "pending", "total_calls_scheduled": 2}
```

---

## Support

For issues or questions:
- Check the `/docs` endpoint for interactive API documentation
- Review server logs for detailed error messages
- Ensure ngrok is running for webhook functionality during development
