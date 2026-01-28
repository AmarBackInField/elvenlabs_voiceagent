# ElevenLabs Voice Agent API

A comprehensive FastAPI wrapper for ElevenLabs Conversational AI platform with support for e-commerce integrations, email templates, batch calling campaigns, and more.

## Features

- **Agent Management**: Create, update, delete, and list AI agents
- **E-Commerce Tools**: WooCommerce and Shopify integration for product/order lookups during calls
- **Knowledge Base**: Ingest documents from text, URL, or file uploads
- **Email Templates**: Create email templates that agents can use during calls
- **Phone Numbers**: Import and manage phone numbers from Twilio/SIP providers
- **Outbound Calls**: Make calls via Twilio or SIP trunk
- **Batch Calling**: Run campaigns with multiple recipients
- **Conversations**: Track and retrieve conversation history

## Quick Start

### Prerequisites

- Python 3.9+
- ElevenLabs API Key
- Twilio Account (for phone calls)
- ngrok (for development webhooks)

### Installation

```bash
# Clone the repository
git clone https://github.com/AmarBackInField/elvenlabs_voiceagent.git
cd elvenlabs_voiceagent

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export ELEVENLABS_API_KEY=your_api_key_here
```

### Running the Server

```bash
# Start the API server
python api/main.py

# In another terminal, start ngrok for webhooks
ngrok http 8000
```

### API Documentation

Once running, access the interactive API docs at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

| Category | Endpoint | Description |
|----------|----------|-------------|
| Agents | `/api/v1/agents` | Create and manage AI agents |
| Tools | `/api/v1/tools` | Create webhook tools for agents |
| Knowledge Base | `/api/v1/knowledge-base` | Ingest documents |
| Email Templates | `/api/v1/email-templates` | Create email templates |
| Phone Numbers | `/api/v1/phone-numbers` | Import Twilio numbers |
| SIP Trunk | `/api/v1/sip-trunk` | Configure SIP trunks |
| Batch Calling | `/api/v1/batch-calling` | Run calling campaigns |
| Conversations | `/api/v1/conversations` | View call history |
| E-commerce | `/api/v1/ecommerce` | Product/order lookups |

## User Flow

```
1. Create Tools (e-commerce, custom webhooks)
2. Create Knowledge Base Documents
3. Create Email Templates
4. Create Agent with tools & knowledge base
5. Import Phone Number (Twilio/SIP)
6. Assign Agent to Phone Number
7. Make Calls (single or batch campaign)
```

## Documentation

See [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) for complete API reference with request/response examples.

## Project Structure

```
elvenlabs_voiceagent/
├── api/
│   ├── main.py              # FastAPI application
│   ├── dependencies.py      # Dependency injection
│   ├── schemas.py           # Pydantic models
│   └── routers/
│       ├── agents.py        # Agent endpoints
│       ├── tools.py         # Tool endpoints
│       ├── knowledge_base.py
│       ├── email_templates.py
│       ├── phone_numbers.py
│       ├── sip_trunk.py
│       ├── batch_calling.py
│       ├── conversations.py
│       ├── ecommerce.py
│       └── webhooks.py
├── client.py                # ElevenLabs API client
├── config.py                # Configuration
├── email_templates.py       # Email template service
├── ecommerce.py             # E-commerce service
├── tools.py                 # Tools service
├── agents.py                # Agents service
└── requirements.txt
```

## License

MIT License
