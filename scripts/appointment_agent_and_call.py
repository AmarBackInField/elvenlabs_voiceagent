#!/usr/bin/env python3
"""
Create appointment email template (with sender_email), create appointment agent,
and place outbound call. Asks customer for preferred date and time only.
Uses customer_email from dynamic variables for confirmation.
Run with API server running: python3 scripts/appointment_agent_and_call.py
"""
import os
import sys
import json
import requests

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
RENDER_URL = "https://elvenlabs-voiceagent.onrender.com"
PHONE_NUMBER_ID = "phnum_1701kh3dxbkxfqyranym0h75402a"
TO_NUMBER = "+919911062767"
SENDER_EMAIL = "amarc8399@gmail.com"
WEBHOOK_BASE_URL = "https://elvenlabs-voiceagent.onrender.com/api/v1"
# Dynamic variable: email where confirmation is sent (injected into call context)
CUSTOMER_EMAIL = "amar_c@me.iitr.ac.in"


def main():
    print(f"Using API base: {BASE_URL}\n")

    # 1. Create appointment email template with sender_email
    print("1. Creating appointment confirmation email template...")
    template_payload = {
        "name": "appointment_confirmation",
        "description": "Send a confirmation email when the customer confirms an appointment. Use after the customer agrees on date and time. Use customer_email from dynamic variables for the email parameter.",
        "subject_template": "Appointment Confirmed",
        "body_template": "Your appointment has been confirmed.\n\nDate: {{date}}\nTime: {{time}}\n\nWe look forward to seeing you.\n\nBest regards",
        "parameters": [
            {"name": "date", "description": "Appointment date", "required": True},
            {"name": "time", "description": "Appointment time", "required": True},
            {"name": "email", "description": "Customer email (use customer_email from dynamic variables)", "required": True},
        ],
        "sender_email": SENDER_EMAIL,
        "webhook_base_url": WEBHOOK_BASE_URL,
    }
    r = requests.post(
        f"{BASE_URL}/api/v1/email-templates",
        json=template_payload,
        timeout=30,
    )
    if r.status_code not in (200, 201):
        print(f"Failed to create template on local: {r.status_code} - {r.text}")
        sys.exit(1)
    template = r.json()
    tool_id = template.get("tool_id")
    if not tool_id:
        print("Template created but no tool_id in response:", template)
        sys.exit(1)
    print(f"   Template ID: {template.get('template_id')}, Tool ID: {tool_id}")
    
    # Also create template on Render (where webhook will be called)
    print("   Creating template on Render server...")
    r2 = requests.post(
        f"{RENDER_URL}/api/v1/email-templates",
        json=template_payload,
        timeout=30,
    )
    if r2.status_code not in (200, 201):
        print(f"   Warning: Failed to create template on Render: {r2.status_code} - {r2.text}")
    else:
        print(f"   Template also created on Render\n")

    # 2. Create appointment agent with this tool
    print("2. Creating appointment agent...")
    agent_payload = {
        "name": "Appointment Agent",
        "first_message": "Hello! This is the appointment service. I'm calling to help you book an appointment. What is your preferred date and time?",
        "system_prompt": (
            "You are a friendly appointment booking agent. Your goals:\n"
            "1. Greet the customer and ask for their preferred appointment date and time only.\n"
            "2. Confirm the date and time back to them.\n"
            "3. Once they confirm, use the appointment_confirmation tool with date and time. For the email parameter, use the customer_email from dynamic variables (it is already provided in the call context).\n"
            "4. Thank them and end the call politely.\n"
            "Be concise and professional. Do not ask for name or email—only preferred date and time."
        ),
        "language": "en",
        "tool_ids": [tool_id],
    }
    r = requests.post(
        f"{BASE_URL}/api/v1/agents",
        json=agent_payload,
        timeout=30,
    )
    if r.status_code not in (200, 201):
        print(f"Failed to create agent: {r.status_code} - {r.text}")
        sys.exit(1)
    agent = r.json()
    agent_id = agent.get("agent_id")
    if not agent_id:
        print("Agent created but no agent_id in response:", agent)
        sys.exit(1)
    print(f"   Agent ID: {agent_id}\n")

    # 3. Place outbound call
    print("3. Placing outbound call to", TO_NUMBER, "...")
    call_payload = {
        "agent_id": agent_id,
        "agent_phone_number_id": PHONE_NUMBER_ID,
        "to_number": TO_NUMBER,
        "customer_info": {
            "name": "Customer",
            "email": CUSTOMER_EMAIL,
        },
        "sender_email": SENDER_EMAIL,
        "dynamic_variables": {"customer_email": CUSTOMER_EMAIL},
    }
    r = requests.post(
        f"{BASE_URL}/api/v1/phone-numbers/twilio/outbound-call",
        json=call_payload,
        timeout=30,
    )
    if r.status_code not in (200, 201):
        print(f"Failed to place call: {r.status_code} - {r.text}")
        sys.exit(1)
    result = r.json()
    print("   Call initiated:", json.dumps(result, indent=2))
    print("\nDone. You should receive the call shortly.")


if __name__ == "__main__":
    main()
