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

RENDER_URL = "https://elvenlabs-voiceagent.onrender.com"
BASE_URL = os.getenv("API_BASE_URL", RENDER_URL)
PHONE_NUMBER_ID = "phnum_1701kh3dxbkxfqyranym0h75402a"
TO_NUMBER = "+919911062767"
SENDER_EMAIL = "amarc8399@gmail.com"
WEBHOOK_BASE_URL = f"{RENDER_URL}/api/v1"
# Dynamic variable: email where confirmation is sent (injected into call context)
CUSTOMER_EMAIL = "amar_c@me.iitr.ac.in"


def main():
    print(f"Using API base: {BASE_URL}\n")

    # 1. Create appointment email template with sender_email
    print("1. Creating appointment confirmation email template...")
    template_payload = {
        "name": "appointment_confirmation",
        "description": "Send a confirmation email when the customer confirms an appointment. Use after the customer agrees on date and time. Email will be retrieved from batch recipient data or dynamic variables.",
        "subject_template": "Appointment Confirmed - {{date}} at {{time}}",
        "body_template": "Hello,\n\nYour appointment has been confirmed.\n\nDate: {{date}}\nTime: {{time}}\n\nWe look forward to seeing you.\n\nBest regards",
        "parameters": [
            {"name": "date", "description": "Appointment date", "required": True},
            {"name": "time", "description": "Appointment time", "required": True},
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
    if BASE_URL != RENDER_URL:
        r2 = requests.post(
            f"{RENDER_URL}/api/v1/email-templates",
            json=template_payload,
            timeout=30,
        )
        if r2.status_code not in (200, 201):
            print(f"   Warning: Failed to create template on Render: {r2.status_code} - {r2.text}")
        else:
            print(f"   Template also created on Render\n")
    else:
        print(f"   Using same server for webhook\n")

    # 2. Create appointment agent with this tool
    print("2. Creating appointment agent...")
    agent_payload = {
        "name": "Appointment Agent",
        "first_message": "Hello! This is the appointment service. I'm calling to help you book an appointment. What is your preferred date and time?",
        "system_prompt": (
            "You are a friendly appointment booking agent. Your goals:\n"
            "1. Greet the customer and ask for their preferred appointment date and time.\n"
            "2. Confirm the date and time back to them.\n"
            "3. Once they confirm, use the appointment_confirmation tool with ONLY the date and time parameters. Do NOT ask for or include email - it is already available in the system.\n"
            "4. After successfully booking, thank them and end the call politely.\n"
            "Be concise and professional. Only ask for date and time."
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

    # 3. Start batch call with recipients (each with name, email, phone, and dynamic_variables)
    print("3. Starting batch call with recipients...")
    batch_payload = {
        "call_name": "Appointment Booking Campaign",
        "agent_id": agent_id,
        "phone_number_id": PHONE_NUMBER_ID,
        "recipients": [
            {
                "phone_number": TO_NUMBER,
                "name": "Customer",
                "email": CUSTOMER_EMAIL,
                "dynamic_variables": {
                    "customer_email": CUSTOMER_EMAIL,
                    "customer_name": "Customer",
                },
            }
        ],
        "sender_email": SENDER_EMAIL,
    }
    r = requests.post(
        f"{BASE_URL}/api/v1/batch-calling/submit",
        json=batch_payload,
        timeout=30,
    )
    if r.status_code not in (200, 201):
        print(f"Failed to submit batch job: {r.status_code} - {r.text}")
        sys.exit(1)
    result = r.json()
    print("   Batch job submitted:", json.dumps(result, indent=2))
    print("\nDone. The calls will be placed shortly.")
    
    # # Alternative: Direct outbound call (commented out)
    # print("3. Placing outbound call to", TO_NUMBER, "...")
    # call_payload = {
    #     "agent_id": agent_id,
    #     "agent_phone_number_id": PHONE_NUMBER_ID,
    #     "to_number": TO_NUMBER,
    # }
    # r = requests.post(
    #     f"{BASE_URL}/api/v1/phone-numbers/twilio/outbound-call",
    #     json=call_payload,
    #     timeout=30,
    # )
    # if r.status_code not in (200, 201):
    #     print(f"Failed to place call: {r.status_code} - {r.text}")
    #     sys.exit(1)
    # result = r.json()
    # print("   Call initiated:", json.dumps(result, indent=2))
    # print("\nDone. You should receive the call shortly.")


if __name__ == "__main__":
    main()
