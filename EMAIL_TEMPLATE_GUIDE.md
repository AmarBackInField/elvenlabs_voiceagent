# Email Template & Batch Calling Guide

This guide explains how to create email templates, connect them to agents, and use batch calling to test email functionality during voice calls.

## Overview

The system allows you to:
1. Create email templates with dynamic placeholders
2. Auto-generate ElevenLabs webhook tools for each template
3. Connect tools to agents so they can send emails during calls
4. Use batch calling to test with multiple recipients

---

## API Endpoints

| Step | Endpoint | Method |
|------|----------|--------|
| Create Email Template | `/api/v1/email-templates` | POST |
| Create Agent | `/api/v1/agents` | POST |
| Update Agent Tools | `/api/v1/agents/{agent_id}/prompt` | PATCH |
| Submit Batch Call | `/api/v1/batch-calling/submit` | POST |

---

## Step 1: Create Email Template

Creates an email template and automatically generates a webhook tool in ElevenLabs.

### Endpoint
```
POST https://elvenlabs-voiceagent.onrender.com/api/v1/email-templates
```

### Request Body
```json
{
  "name": "booking_appointment",
  "description": "Use this tool when a customer confirms or books an appointment. Send them a confirmation email with the appointment details.",
  "subject_template": "Your Appointment is Confirmed - {{date}} at {{time}}",
  "body_template": "Dear {{customer_name}},\n\nThank you for booking an appointment with us!\n\nHere are your appointment details:\n\n📅 Date: {{date}}\n⏰ Time: {{time}}\n📧 Email: {{customer_email}}\n\nPlease make sure to arrive 10 minutes before your scheduled time.\n\nIf you need to reschedule or cancel, please contact us.\n\nBest regards,\nAistein Team",
  "parameters": [
    {"name": "date", "description": "The date of the appointment (e.g., February 5, 2026)", "required": true},
    {"name": "time", "description": "The time of the appointment (e.g., 2:30 PM)", "required": true}
  ],
  "webhook_base_url": "https://elvenlabs-voiceagent.onrender.com/api/v1"
}
```

### Template Placeholders

| Placeholder | Source | Description |
|-------------|--------|-------------|
| `{{customer_name}}` | Auto-filled from recipient info | Customer's name |
| `{{customer_email}}` | Auto-filled from recipient info | Customer's email |
| `{{date}}` | Provided by AI during call | Appointment date |
| `{{time}}` | Provided by AI during call | Appointment time |

### Response
```json
{
  "template_id": "booking_appointment",
  "name": "booking_appointment",
  "description": "Use this tool when a customer confirms or books an appointment...",
  "subject_template": "Your Appointment is Confirmed - {{date}} at {{time}}",
  "body_template": "Dear {{customer_name}},...",
  "parameters": [...],
  "tool_id": "tool_5501kgfh12q8e12bps9k6tx36ayb",
  "created_at": "2026-02-02T15:55:03.693328"
}
```

### What Happens Internally

1. Template is stored in memory
2. A webhook tool is created in ElevenLabs with:
   - URL: `https://elvenlabs-voiceagent.onrender.com/api/v1/webhooks/email/booking_appointment`
   - System parameters: `conversation_id`, `agent_id`, `called_number`
   - Custom parameters: `date`, `time`

---

## Step 2: Create Agent with Tool

Creates an agent and connects the email template tool.

### Endpoint
```
POST https://elvenlabs-voiceagent.onrender.com/api/v1/agents
```

### Request Body
```json
{
  "name": "Appointment Booking Agent",
  "first_message": "Hello! This is the Aistein appointment service. I am calling to help you book an appointment. May I know your preferred date and time?",
  "system_prompt": "You are a friendly and professional appointment booking agent for Aistein. Your goal is to help customers book appointments.\n\nWhen the customer confirms their appointment date and time, you MUST use the booking_appointment tool to send them a confirmation email.\n\nAlways:\n1. Greet the customer warmly\n2. Ask for their preferred date and time\n3. Confirm the details with them\n4. Once confirmed, use the booking_appointment tool to send the confirmation email\n5. Thank them and end the call professionally\n\nBe conversational, helpful, and efficient.",
  "language": "en",
  "tool_ids": ["tool_5501kgfh12q8e12bps9k6tx36ayb"]
}
```

### Response
```json
{
  "agent_id": "agent_1101kgfgeh9bf9yvxrpbncj94emb"
}
```

### Updating an Existing Agent's Tools

If you already have an agent and want to add/update tools:

```
PATCH https://elvenlabs-voiceagent.onrender.com/api/v1/agents/{agent_id}/prompt
```

```json
{
  "tool_ids": ["tool_5501kgfh12q8e12bps9k6tx36ayb"]
}
```

---

## Step 3: Submit Batch Call

Submits a batch calling job to call recipients.

### Endpoint
```
POST https://elvenlabs-voiceagent.onrender.com/api/v1/batch-calling/submit
```

### Request Body
```json
{
  "call_name": "Appointment Booking Test - Amar",
  "agent_id": "agent_1101kgfgeh9bf9yvxrpbncj94emb",
  "phone_number_id": "phnum_7501kgfddb70fxysd2gqa3vrhcjh",
  "recipients": [
    {
      "phone_number": "+919911062767",
      "name": "Amar",
      "email": "amar_c@me.iitr.ac.in",
      "dynamic_variables": {
        "customer_name": "Amar",
        "name": "Amar"
      }
    }
  ],
  "sender_email": "amarc8399@gmail.com"
}
```

### Request Parameters

| Field | Required | Description |
|-------|----------|-------------|
| `call_name` | Yes | Name/label for the batch job |
| `agent_id` | Yes | Agent to handle the calls |
| `phone_number_id` | Yes | Your Twilio phone number ID for caller ID |
| `recipients` | Yes | Array of people to call |
| `recipients[].phone_number` | Yes | Phone number in E.164 format |
| `recipients[].name` | No | Recipient's name (used in email templates) |
| `recipients[].email` | No | Recipient's email (required for email templates) |
| `recipients[].dynamic_variables` | No | Variables available during the call |
| `sender_email` | No | Email address for the "from" field |

### Response
```json
{
  "id": "btcal_3201kgfh1ew8fk7bz0zrntr8asda",
  "name": "Appointment Booking Test - Amar",
  "agent_id": "agent_1101kgfgeh9bf9yvxrpbncj94emb",
  "status": "pending",
  "phone_number_id": "phnum_7501kgfddb70fxysd2gqa3vrhcjh",
  "phone_provider": "twilio",
  "total_calls_scheduled": 1,
  "total_calls_dispatched": 0,
  "total_calls_finished": 0
}
```

---

## Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│  1. POST /email-templates                                                │
│     → Creates template + webhook tool in ElevenLabs                      │
│     → Returns tool_id                                                    │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  2. POST /agents                                                         │
│     → Creates agent with tool_ids array                                  │
│     → Returns agent_id                                                   │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  3. POST /batch-calling/submit                                           │
│     → Stores recipient info: phone → {name, email}                      │
│     → Submits job to ElevenLabs                                          │
│     → ElevenLabs calls recipient via Twilio                             │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  4. During call, agent uses booking_appointment tool                     │
│     → ElevenLabs calls: POST /webhooks/email/booking_appointment        │
│     → Body: {conversation_id, agent_id, called_number, date, time}      │
│     → Webhook looks up recipient by called_number                       │
│     → Sends email via external email API                                │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## How the Email Webhook Works

When the agent uses the email tool during a call, ElevenLabs sends a POST request to:

```
POST /api/v1/webhooks/email/booking_appointment
```

With body:
```json
{
  "conversation_id": "conv_xxx",
  "agent_id": "agent_xxx",
  "called_number": "+919911062767",
  "date": "February 6, 2026",
  "time": "6:00 PM"
}
```

The webhook:
1. Extracts `called_number` from the request
2. Looks up recipient info from the batch job context
3. Finds: `+919911062767 → {"name": "Amar", "email": "amar_c@me.iitr.ac.in"}`
4. Fills the email template with customer info + parameters
5. Sends the email via external API

---

## System Dynamic Variables

These are automatically provided by ElevenLabs and mapped to tool parameters:

| Variable | Description |
|----------|-------------|
| `system__conversation_id` | Unique conversation identifier |
| `system__agent_id` | Agent handling the call |
| `system__called_number` | Recipient's phone number |
| `system__caller_id` | Your outbound phone number |
| `system__call_duration_secs` | Call duration in seconds |
| `system__time_utc` | Current UTC time |

---

## Troubleshooting

### "No customer info found" Error

**Cause:** The webhook couldn't find recipient info because the phone number wasn't passed.

**Solution:** Ensure the email template tool includes `called_number` parameter with `dynamic_variable: "system__called_number"`. This was fixed in the code update on 2026-02-02.

### Email Not Sending

**Checklist:**
1. Recipient has `email` field in batch call request
2. `sender_email` is provided
3. External email API is accessible
4. Template exists and is not deleted

### Tool Not Working

**Checklist:**
1. Tool ID is correct and exists
2. Agent has the tool in `tool_ids` array
3. Webhook URL is accessible from ElevenLabs servers

---

## Example: Full cURL Commands

### 1. Create Template
```bash
curl -X POST "https://elvenlabs-voiceagent.onrender.com/api/v1/email-templates" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "booking_appointment",
    "description": "Send appointment confirmation email",
    "subject_template": "Appointment Confirmed - {{date}} at {{time}}",
    "body_template": "Dear {{customer_name}},\n\nYour appointment is confirmed for {{date}} at {{time}}.\n\nBest regards",
    "parameters": [
      {"name": "date", "description": "Appointment date", "required": true},
      {"name": "time", "description": "Appointment time", "required": true}
    ],
    "webhook_base_url": "https://elvenlabs-voiceagent.onrender.com/api/v1"
  }'
```

### 2. Create Agent
```bash
curl -X POST "https://elvenlabs-voiceagent.onrender.com/api/v1/agents" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Booking Agent",
    "first_message": "Hello! I am calling to help you book an appointment.",
    "system_prompt": "Help customers book appointments. Use booking_appointment tool to send confirmation.",
    "tool_ids": ["tool_xxx"]
  }'
```

### 3. Submit Batch Call
```bash
curl -X POST "https://elvenlabs-voiceagent.onrender.com/api/v1/batch-calling/submit" \
  -H "Content-Type: application/json" \
  -d '{
    "call_name": "Test Call",
    "agent_id": "agent_xxx",
    "phone_number_id": "phnum_xxx",
    "recipients": [
      {
        "phone_number": "+919911062767",
        "name": "Amar",
        "email": "amar@example.com"
      }
    ],
    "sender_email": "sender@example.com"
  }'
```

---

## Related Files

| File | Purpose |
|------|---------|
| `email_templates.py` | Email template service and tool creation |
| `api/routers/email_templates.py` | REST API endpoints for templates |
| `api/routers/webhooks.py` | Webhook handlers called by ElevenLabs |
| `api/routers/batch_calling.py` | Batch calling API endpoints |
| `ecommerce.py` | Contains `BatchJobContextStore` for recipient lookup |
