# Email Template Tool Setup Guide

This guide explains how to set up and use email template tools with ElevenLabs voice agents.

## Base URL

**Production:** `https://elvenlabs-voiceagent.onrender.com`  
**Local:** `http://127.0.0.1:8000`

---

## Complete Setup Flow

### Step 1: Create Email Template

This creates both the template AND registers a webhook tool in ElevenLabs.

```bash
curl -X POST "https://elvenlabs-voiceagent.onrender.com/api/v1/email-templates" \
  -H "Content-Type: application/json" \
  -d '{
  "name": "booking_confirmation",
  "description": "Send booking confirmation email after collecting customer name and email",
  "subject_template": "Your Appointment Has Been Booked - {{name}}",
  "body_template": "Dear {{name}},\n\nThank you for booking your appointment with us!\n\nConfirmation sent to: {{email}}\n\nBest regards,\nThe Booking Team",
  "webhook_base_url": "https://elvenlabs-voiceagent.onrender.com/api/v1"
}'
```

**Response:**
```json
{
  "template_id": "booking_confirmation",
  "name": "booking_confirmation",
  "description": "Send booking confirmation email after collecting customer name and email",
  "subject_template": "Your Appointment Has Been Booked - {{name}}",
  "body_template": "Dear {{name}},\n\nThank you for booking...",
  "parameters": [],
  "tool_id": "tool_xxxxx",
  "created_at": "2026-01-30T18:34:34.937236"
}
```

> **Important:** Save the `tool_id` - you'll need it for creating the agent.

---

### Step 2: Create Agent with the Tool

```bash
curl -X POST "https://elvenlabs-voiceagent.onrender.com/api/v1/agents" \
  -H "Content-Type: application/json" \
  -d '{
  "name": "Booking Agent",
  "first_message": "Hello! I can help you book an appointment. May I have your name please?",
  "system_prompt": "You are a friendly booking assistant.\n\nYour workflow:\n1. Ask for customer name\n2. Ask for email address\n3. Confirm both details by repeating them back\n4. Once confirmed, call the send_booking_confirmation tool\n5. Tell the customer the confirmation email was sent\n\nBe conversational and helpful.",
  "language": "en",
  "tool_ids": ["tool_xxxxx"]
}'
```

> Replace `tool_xxxxx` with the actual tool_id from Step 1.

**Response:**
```json
{
  "agent_id": "agent_xxxxx"
}
```

---

### Step 3: Assign Phone Number to Agent

```bash
curl -X PATCH "https://elvenlabs-voiceagent.onrender.com/api/v1/phone-numbers/{phone_number_id}" \
  -H "Content-Type: application/json" \
  -d '{
  "agent_id": "agent_xxxxx"
}'
```

> Replace `{phone_number_id}` with your Twilio phone number ID and `agent_xxxxx` with the agent ID from Step 2.

**Response:**
```json
{
  "phone_number_id": "phnum_xxxxx",
  "phone_number": "+12625925656",
  "assigned_agent": {
    "agent_id": "agent_xxxxx",
    "agent_name": "Booking Agent"
  }
}
```

---

### Step 4: Make Outbound Call

```bash
curl -X POST "https://elvenlabs-voiceagent.onrender.com/api/v1/phone-numbers/twilio/outbound-call" \
  -H "Content-Type: application/json" \
  -d '{
  "agent_id": "agent_xxxxx",
  "agent_phone_number_id": "phnum_xxxxx",
  "to_number": "+919911062767"
}'
```

**Response:**
```json
{
  "success": true,
  "message": "Call initiated successfully",
  "conversation_id": "conv_xxxxx"
}
```

---

## Quick Reference: Your Current Setup

| Component | ID |
|-----------|-----|
| Phone Number | `phnum_5901kg7vntrsej3aff74xt7e3eq6` |
| Phone Number Value | `+12625925656` |

---

## Re-Setup After Server Restart/Redeploy

Email templates are stored **in-memory** and will be lost when the server restarts. However, the ElevenLabs tool persists.

After each redeploy, only recreate the template with the **same name** the tool expects:

```bash
curl -X POST "https://elvenlabs-voiceagent.onrender.com/api/v1/email-templates" \
  -H "Content-Type: application/json" \
  -d '{
  "name": "booking_confirmation",
  "description": "Send booking confirmation email",
  "subject_template": "Your Appointment Has Been Booked - {{name}}",
  "body_template": "Dear {{name}},\n\nConfirmation sent to: {{email}}\n\nBest regards",
  "webhook_base_url": "https://elvenlabs-voiceagent.onrender.com/api/v1"
}'
```

> The `name` field MUST match the template_id that the ElevenLabs tool expects.

---

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `404 Not Found` | Webhook URL path mismatch | Ensure server is running and URL is correct |
| `Template not found` | Server restarted, in-memory templates lost | Recreate the template with the same name |
| `Unable to execute function` | Webhook unreachable | Check if server is awake (Render cold start) |
| Webhook timeout | Render server sleeping | Visit `/docs` to wake up server, then retry |

---

## Template Variables

Email templates support placeholders using `{{variable}}` syntax:

| Variable | Description | Source |
|----------|-------------|--------|
| `{{name}}` | Customer name | Extracted from conversation |
| `{{email}}` | Customer email | Extracted from conversation |
| `{{customer_name}}` | Alias for name | Auto-filled from session |
| `{{customer_email}}` | Alias for email | Auto-filled from session |

---

## API Endpoints Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/email-templates` | POST | Create email template |
| `/api/v1/email-templates` | GET | List all templates |
| `/api/v1/email-templates/{id}` | GET | Get template by ID |
| `/api/v1/email-templates/{id}` | DELETE | Delete template |
| `/api/v1/agents` | POST | Create agent |
| `/api/v1/agents/{id}` | GET | Get agent |
| `/api/v1/agents/{id}/prompt` | PATCH | Update agent prompt/tools |
| `/api/v1/phone-numbers/{id}` | PATCH | Assign agent to phone number |
| `/api/v1/phone-numbers/twilio/outbound-call` | POST | Make outbound call |

---

## Example: Complete Setup Script

```bash
#!/bin/bash

BASE_URL="https://elvenlabs-voiceagent.onrender.com"
PHONE_NUMBER_ID="phnum_5901kg7vntrsej3aff74xt7e3eq6"
TO_NUMBER="+919911062767"

# Step 1: Create Email Template
echo "Creating email template..."
TEMPLATE_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/email-templates" \
  -H "Content-Type: application/json" \
  -d '{
  "name": "booking_confirmation",
  "description": "Send booking confirmation email",
  "subject_template": "Appointment Booked - {{name}}",
  "body_template": "Dear {{name}},\n\nConfirmation sent to: {{email}}\n\nBest regards",
  "webhook_base_url": "'$BASE_URL'/api/v1"
}')

TOOL_ID=$(echo $TEMPLATE_RESPONSE | grep -o '"tool_id":"[^"]*"' | cut -d'"' -f4)
echo "Tool ID: $TOOL_ID"

# Step 2: Create Agent
echo "Creating agent..."
AGENT_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/agents" \
  -H "Content-Type: application/json" \
  -d '{
  "name": "Booking Agent",
  "first_message": "Hello! May I have your name please?",
  "system_prompt": "You are a booking assistant. Collect name and email, confirm, then send confirmation.",
  "language": "en",
  "tool_ids": ["'$TOOL_ID'"]
}')

AGENT_ID=$(echo $AGENT_RESPONSE | grep -o '"agent_id":"[^"]*"' | cut -d'"' -f4)
echo "Agent ID: $AGENT_ID"

# Step 3: Assign Phone Number
echo "Assigning phone number..."
curl -s -X PATCH "$BASE_URL/api/v1/phone-numbers/$PHONE_NUMBER_ID" \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "'$AGENT_ID'"}'

# Step 4: Make Call
echo "Making outbound call..."
curl -s -X POST "$BASE_URL/api/v1/phone-numbers/twilio/outbound-call" \
  -H "Content-Type: application/json" \
  -d '{
  "agent_id": "'$AGENT_ID'",
  "agent_phone_number_id": "'$PHONE_NUMBER_ID'",
  "to_number": "'$TO_NUMBER'"
}'

echo "Done!"
```

---

## Production Recommendations

1. **Persist Templates**: For production, modify the email template service to store templates in a database instead of in-memory.

2. **Health Check Endpoint**: Add a health check endpoint that warms up the template cache on startup.

3. **Environment Variables**: Store sensitive configuration (API keys, webhook URLs) in environment variables.

4. **Logging**: Monitor webhook calls and errors for debugging.
