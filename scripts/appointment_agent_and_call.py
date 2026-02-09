#!/usr/bin/env python3
"""
Create appointment email template (with sender_email), create appointment agent,
and place outbound call to Amar.
Run with API server running: python3 scripts/appointment_agent_and_call.py
"""
import os
import sys
import json
import requests

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
PHONE_NUMBER_ID = "phnum_4801kh0dka0pe0ktk0zt19s577g7"
TO_NUMBER = "+919911062767"
CUSTOMER_NAME = "Amar"
SENDER_EMAIL = "amarc8399@gmail.com"


def main():
    print(f"Using API base: {BASE_URL}\n")

    # 1. Create appointment email template with sender_email
    print("1. Creating appointment confirmation email template...")
    template_payload = {
        "name": "appointment_confirmation",
        "description": "Send a confirmation email when the customer confirms an appointment. Use after the customer agrees on date and time.",
        "subject_template": "Appointment Confirmed – {{name}}",
        "body_template": "Dear {{name}},\n\nYour appointment has been confirmed.\n\nDate: {{date}}\nTime: {{time}}\n\nWe look forward to seeing you.\n\nBest regards",
        "parameters": [
            {"name": "date", "description": "Appointment date", "required": True},
            {"name": "time", "description": "Appointment time", "required": True},
            {"name": "email", "description": "Customer email address for sending confirmation", "required": True},
            {"name": "name", "description": "Customer name", "required": False},
        ],
        "sender_email": SENDER_EMAIL,
        "webhook_base_url": "https://elvenlabs-voiceagent.onrender.com/api/v1",
    }
    r = requests.post(
        f"{BASE_URL}/api/v1/email-templates",
        json=template_payload,
        timeout=30,
    )
    if r.status_code not in (200, 201):
        print(f"Failed to create template: {r.status_code} - {r.text}")
        sys.exit(1)
    template = r.json()
    tool_id = template.get("tool_id")
    if not tool_id:
        print("Template created but no tool_id in response:", template)
        sys.exit(1)
    print(f"   Template ID: {template.get('template_id')}, Tool ID: {tool_id}\n")

    # 2. Create appointment agent with this tool
    print("2. Creating appointment agent...")
    agent_payload = {
        "name": "Appointment Agent",
        "first_message": "Hello! This is the appointment service. I'm calling to help you book an appointment. May I have your name and preferred date and time?",
        "system_prompt": (
            "You are a friendly appointment booking agent. Your goals:\n"
            "1. Greet the customer and ask for their name.\n"
            "2. Ask for their preferred appointment date and time.\n"
            "3. Ask for their email address to send the confirmation.\n"
            "4. Confirm all details back to them (name, date, time, email).\n"
            "5. Once they confirm, use the appointment_confirmation tool with date, time, email, and name parameters.\n"
            "6. Thank them and end the call politely.\n"
            "Be concise and professional. Always collect the email before calling the tool."
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
            "name": CUSTOMER_NAME,
            "email": SENDER_EMAIL,
        },
        "sender_email": SENDER_EMAIL,
        "dynamic_variables": {"customer_name": CUSTOMER_NAME},
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
