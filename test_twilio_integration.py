#!/usr/bin/env python3
"""
Twilio + ElevenLabs Integration Test Script

This script demonstrates:
1. Creating an ElevenLabs AI agent
2. Importing a Twilio phone number
3. Assigning the agent to the phone number

Prerequisites:
- API server running (python run_api.py)
- Environment variables set in .env file:
  - ELEVENLABS_API_KEY
  - TWILIO_ACCOUNT_SID
  - TWILIO_AUTH_TOKEN
  - TWILIO_NUMBER
"""

import os
import requests
import sys

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"

# Twilio Credentials from environment
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_NUMBER = os.getenv("TWILIO_NUMBER")


def create_agent():
    """Create a test AI agent."""
    print("\n=== Step 1: Creating ElevenLabs Agent ===")
    
    payload = {
        "name": "Twilio Test Agent",
        "first_message": "Hello! This is a test call from ElevenLabs AI. How can I help you today?",
        "system_prompt": "You are a helpful AI assistant. Be friendly and concise.",
        "language": "en"
    }
    
    response = requests.post(f"{API_BASE_URL}/agents", json=payload)
    
    if response.status_code == 201:
        result = response.json()
        agent_id = result.get("agent_id")
        print(f"✓ Agent created successfully!")
        print(f"  Agent ID: {agent_id}")
        return agent_id
    else:
        print(f"✗ Failed to create agent: {response.status_code}")
        print(f"  Error: {response.text}")
        return None


def import_twilio_number():
    """Import Twilio phone number to ElevenLabs."""
    print("\n=== Step 2: Importing Twilio Phone Number ===")
    
    payload = {
        "phone_number": TWILIO_NUMBER,
        "label": "Twilio Test Line",
        "sid": TWILIO_ACCOUNT_SID,
        "token": TWILIO_AUTH_TOKEN
    }
    
    response = requests.post(f"{API_BASE_URL}/phone-numbers", json=payload)
    
    if response.status_code == 201:
        result = response.json()
        phone_number_id = result.get("phone_number_id")
        print(f"✓ Phone number imported successfully!")
        print(f"  Phone Number ID: {phone_number_id}")
        return phone_number_id
    else:
        print(f"✗ Failed to import phone number: {response.status_code}")
        print(f"  Error: {response.text}")
        return None


def assign_agent_to_number(phone_number_id: str, agent_id: str):
    """Assign an agent to handle calls on the phone number."""
    print("\n=== Step 3: Assigning Agent to Phone Number ===")
    
    payload = {
        "agent_id": agent_id
    }
    
    response = requests.patch(
        f"{API_BASE_URL}/phone-numbers/{phone_number_id}",
        json=payload
    )
    
    if response.status_code == 200:
        print(f"✓ Agent assigned to phone number successfully!")
        print(f"  Phone Number: {TWILIO_NUMBER}")
        print(f"  Agent ID: {agent_id}")
        return True
    else:
        print(f"✗ Failed to assign agent: {response.status_code}")
        print(f"  Error: {response.text}")
        return False


def list_phone_numbers():
    """List all imported phone numbers."""
    print("\n=== Listing Phone Numbers ===")
    
    response = requests.get(f"{API_BASE_URL}/phone-numbers")
    
    if response.status_code == 200:
        result = response.json()
        numbers = result.get("phone_numbers", [])
        print(f"Found {len(numbers)} phone number(s):")
        for num in numbers:
            print(f"  - {num.get('phone_number')} (ID: {num.get('phone_number_id')})")
            if num.get('agent_id'):
                print(f"    Assigned Agent: {num.get('agent_id')}")
        return numbers
    else:
        print(f"✗ Failed to list phone numbers: {response.status_code}")
        return []


def list_agents():
    """List all agents."""
    print("\n=== Listing Agents ===")
    
    response = requests.get(f"{API_BASE_URL}/agents")
    
    if response.status_code == 200:
        result = response.json()
        agents = result.get("agents", [])
        print(f"Found {len(agents)} agent(s):")
        for agent in agents:
            print(f"  - {agent.get('name', 'Unnamed')} (ID: {agent.get('agent_id')})")
        return agents
    else:
        print(f"✗ Failed to list agents: {response.status_code}")
        return []


def make_outbound_call(agent_id: str, phone_number_id: str, to_number: str):
    """Initiate an outbound call via SIP trunk."""
    print(f"\n=== Making Outbound Call to {to_number} ===")
    
    payload = {
        "agent_id": agent_id,
        "agent_phone_number_id": phone_number_id,
        "to_number": to_number
    }
    
    response = requests.post(f"{API_BASE_URL}/sip-trunk/outbound-call", json=payload)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Call initiated!")
        print(f"  Conversation ID: {result.get('conversation_id')}")
        return result
    else:
        print(f"✗ Failed to initiate call: {response.status_code}")
        print(f"  Error: {response.text}")
        return None


def main():
    """Run the Twilio integration test."""
    print("=" * 60)
    print("Twilio + ElevenLabs Integration Test")
    print("=" * 60)
    
    # Check Twilio credentials
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_NUMBER]):
        print("✗ Missing Twilio credentials!")
        print("  Please set the following in your .env file:")
        print("    TWILIO_ACCOUNT_SID=your_account_sid")
        print("    TWILIO_AUTH_TOKEN=your_auth_token")
        print("    TWILIO_NUMBER=+1234567890")
        sys.exit(1)
    
    print(f"✓ Twilio credentials loaded for {TWILIO_NUMBER}")
    
    # Check if API is running
    try:
        response = requests.get(f"{API_BASE_URL.replace('/api/v1', '')}/health")
        if response.status_code != 200:
            print("✗ API server is not healthy")
            sys.exit(1)
        print("✓ API server is running")
    except requests.ConnectionError:
        print("✗ Cannot connect to API server at http://localhost:8000")
        print("  Please start the server with: python run_api.py")
        sys.exit(1)
    
    # List existing resources
    list_agents()
    list_phone_numbers()
    
    # Ask user what to do
    print("\n" + "=" * 60)
    print("Options:")
    print("1. Create new agent and import Twilio number")
    print("2. Just list existing resources")
    print("3. Make an outbound test call (requires agent and phone number)")
    print("=" * 60)
    
    choice = input("\nEnter choice (1/2/3): ").strip()
    
    if choice == "1":
        # Step 1: Create agent
        agent_id = create_agent()
        if not agent_id:
            print("\nFailed at Step 1. Exiting.")
            sys.exit(1)
        
        # Step 2: Import Twilio number
        phone_number_id = import_twilio_number()
        if not phone_number_id:
            print("\nFailed at Step 2. Exiting.")
            sys.exit(1)
        
        # Step 3: Assign agent to phone number
        success = assign_agent_to_number(phone_number_id, agent_id)
        if not success:
            print("\nFailed at Step 3. Exiting.")
            sys.exit(1)
        
        print("\n" + "=" * 60)
        print("✓ Setup Complete!")
        print("=" * 60)
        print(f"\nYour Twilio number {TWILIO_NUMBER} is now connected to the AI agent.")
        print("When someone calls this number, the ElevenLabs agent will answer.")
        
    elif choice == "2":
        print("\nListing complete.")
        
    elif choice == "3":
        agent_id = input("Enter Agent ID: ").strip()
        phone_number_id = input("Enter Phone Number ID: ").strip()
        to_number = input("Enter destination number (E.164 format, e.g., +14155551234): ").strip()
        
        if agent_id and phone_number_id and to_number:
            make_outbound_call(agent_id, phone_number_id, to_number)
        else:
            print("Missing required inputs.")
    
    else:
        print("Invalid choice.")


if __name__ == "__main__":
    main()
