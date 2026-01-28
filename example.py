"""
Example usage of ElevenLabs Agent Client.
Demonstrates all major functionality with separate service classes.
"""

from dotenv import load_dotenv

# Unified client approach
from client import ElevenLabsClient

# Individual services approach
from config import ElevenLabsConfig
from agents import AgentService
from phone_numbers import PhoneNumberService
from sip_trunk import SIPTrunkService
from batch_calling import BatchCallingService

from exceptions import ElevenLabsError, NotFoundError, AuthenticationError


def unified_client_example():
    """
    Example using the unified ElevenLabsClient.
    This is the recommended approach for most use cases.
    """
    load_dotenv()
    
    print("\n" + "=" * 60)
    print("UNIFIED CLIENT EXAMPLE")
    print("=" * 60)
    
    # Initialize unified client
    with ElevenLabsClient(log_level="INFO") as client:
        try:
            # =========================================================
            # Agent Management
            # =========================================================
            print("\n--- Agent Management ---")
            
            # Create agent
            agent = client.agents.create_agent(
                name="Customer Support Bot",
                voice_id="21m00Tcm4TlvDq8ikWAM",
                first_message="Hello! How can I help you today?",
                system_prompt="You are a helpful customer support agent."
            )
            agent_id = agent["agent_id"]
            print(f"Created agent: {agent_id}")
            
            # Get agent details
            details = client.agents.get_agent(agent_id)
            print(f"Agent name: {details.get('name')}")
            
            # List all agents
            agents_list = client.agents.list_agents()
            print(f"Total agents: {len(agents_list.get('agents', []))}")
            
            # =========================================================
            # Phone Numbers
            # =========================================================
            print("\n--- Phone Numbers ---")
            
            # Import phone number (Twilio example)
            phone = client.phone_numbers.import_phone_number(
                phone_number="+14155551234",
                label="Main Support Line",
                sid="ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
                token="your_auth_token"
            )
            phone_id = phone["phone_number_id"]
            print(f"Imported phone: {phone_id}")
            
            # Assign agent to phone number
            client.phone_numbers.update_phone_number(
                phone_number_id=phone_id,
                agent_id=agent_id
            )
            print(f"Assigned agent to phone number")
            
            # =========================================================
            # SIP Trunk Outbound Call
            # =========================================================
            print("\n--- SIP Trunk Outbound Call ---")
            
            # Make outbound call
            call = client.sip_trunk.outbound_call(
                agent_id=agent_id,
                agent_phone_number_id=phone_id,
                to_number="+14155559999",
                dynamic_variables={
                    "customer_name": "John Doe",
                    "order_id": "ORD-12345"
                }
            )
            print(f"Call initiated: {call.get('conversation_id')}")
            print(f"SIP Call ID: {call.get('sip_call_id')}")
            
            # =========================================================
            # Batch Calling
            # =========================================================
            print("\n--- Batch Calling ---")
            
            # Submit batch job
            job = client.batch_calling.submit_job(
                call_name="Q1 Customer Outreach",
                agent_id=agent_id,
                phone_number_id=phone_id,
                recipients=[
                    {
                        "phone_number": "+14155551111",
                        "name": "Alice Johnson",
                        "dynamic_variables": {"appointment": "Feb 1, 2026"}
                    },
                    {
                        "phone_number": "+14155552222",
                        "name": "Bob Smith", 
                        "dynamic_variables": {"appointment": "Feb 2, 2026"}
                    },
                    {
                        "phone_number": "+14155553333",
                        "name": "Carol Williams",
                        "dynamic_variables": {"appointment": "Feb 3, 2026"}
                    }
                ],
                retry_count=2
            )
            job_id = job["id"]
            print(f"Batch job submitted: {job_id}")
            print(f"Status: {job['status']}")
            print(f"Scheduled calls: {job.get('total_calls_scheduled', 0)}")
            
            # Get job status
            status = client.batch_calling.get_job(job_id)
            print(f"Progress: {status.get('total_calls_finished', 0)}/{status.get('total_calls_scheduled', 0)}")
            
            # =========================================================
            # Cleanup
            # =========================================================
            print("\n--- Cleanup ---")
            
            client.batch_calling.cancel_job(job_id)
            print("Batch job cancelled")
            
            client.phone_numbers.delete_phone_number(phone_id)
            print("Phone number deleted")
            
            client.agents.delete_agent(agent_id)
            print("Agent deleted")
            
            print("\n" + "=" * 60)
            print("EXAMPLE COMPLETED SUCCESSFULLY!")
            print("=" * 60)
            
        except AuthenticationError as e:
            print(f"\nAuthentication failed: {e}")
            print("Please check your API key.")
            
        except ElevenLabsError as e:
            print(f"\nAPI error: {e}")


def individual_services_example():
    """
    Example using individual service classes.
    Useful when you need fine-grained control or only specific functionality.
    """
    load_dotenv()
    
    print("\n" + "=" * 60)
    print("INDIVIDUAL SERVICES EXAMPLE")
    print("=" * 60)
    
    # Create shared configuration
    config = ElevenLabsConfig.from_env()
    
    # Initialize only the services you need
    agent_service = AgentService(config)
    batch_service = BatchCallingService(config)
    
    try:
        # Create agent using agent service
        print("\n--- Creating Agent ---")
        agent = agent_service.create_agent(
            conversation_config={
                "agent": {
                    "first_message": "Hi! I'm your AI assistant.",
                    "language": "en",
                    "prompt": {
                        "prompt": "You are a helpful assistant that answers questions."
                    }
                },
                "tts": {
                    "voice_id": "21m00Tcm4TlvDq8ikWAM"
                }
            }
        )
        agent_id = agent["agent_id"]
        print(f"Agent created: {agent_id}")
        
        # Get agent details
        details = agent_service.get_agent(agent_id)
        print(f"Agent retrieved successfully")
        
        # Submit batch job
        print("\n--- Submitting Batch Job ---")
        job = batch_service.submit_job(
            call_name="Test Campaign",
            agent_id=agent_id,
            recipients=[
                {"phone_number": "+14155551234"}
            ]
        )
        print(f"Job submitted: {job['id']}")
        
        # Cleanup
        print("\n--- Cleanup ---")
        batch_service.cancel_job(job["id"])
        agent_service.delete_agent(agent_id)
        print("Cleanup completed")
        
    except ElevenLabsError as e:
        print(f"Error: {e}")
        
    finally:
        # Close service sessions
        agent_service.close()
        batch_service.close()


def batch_campaign_workflow():
    """
    Complete workflow example for running a batch calling campaign.
    """
    load_dotenv()
    
    print("\n" + "=" * 60)
    print("BATCH CAMPAIGN WORKFLOW")
    print("=" * 60)
    
    # Campaign data
    campaign_name = "Product Launch Announcement"
    contacts = [
        {"phone": "+14155551234", "name": "John", "product": "Widget Pro"},
        {"phone": "+14155555678", "name": "Jane", "product": "Widget Pro"},
        {"phone": "+14155559012", "name": "Bob", "product": "Widget Pro"},
    ]
    
    with ElevenLabsClient(log_level="INFO") as client:
        try:
            # Step 1: Create campaign agent
            print("\n1. Creating campaign agent...")
            agent = client.agents.create_agent(
                name=f"Agent - {campaign_name}",
                voice_id="21m00Tcm4TlvDq8ikWAM",
                first_message="Hello {{name}}! I'm calling about our new {{product}}.",
                system_prompt="""You are a friendly sales representative announcing a new product.
                Be enthusiastic but not pushy. Answer questions about the product.
                If they're not interested, thank them politely and end the call."""
            )
            agent_id = agent["agent_id"]
            print(f"   Agent created: {agent_id}")
            
            # Step 2: Prepare recipients
            print("\n2. Preparing recipients...")
            recipients = [
                {
                    "phone_number": contact["phone"],
                    "name": contact["name"],
                    "dynamic_variables": {
                        "name": contact["name"],
                        "product": contact["product"]
                    }
                }
                for contact in contacts
            ]
            print(f"   {len(recipients)} recipients prepared")
            
            # Step 3: Submit batch job
            print("\n3. Submitting batch job...")
            job = client.batch_calling.submit_job(
                call_name=campaign_name,
                agent_id=agent_id,
                recipients=recipients,
                retry_count=2  # Retry failed calls up to 2 times
            )
            job_id = job["id"]
            print(f"   Job submitted: {job_id}")
            print(f"   Status: {job['status']}")
            
            # Step 4: Monitor progress
            print("\n4. Monitoring progress...")
            import time
            max_checks = 5
            for i in range(max_checks):
                status = client.batch_calling.get_job(job_id)
                dispatched = status.get("total_calls_dispatched", 0)
                scheduled = status.get("total_calls_scheduled", 0)
                finished = status.get("total_calls_finished", 0)
                
                print(f"   Check {i+1}: Dispatched={dispatched}, "
                      f"Scheduled={scheduled}, Finished={finished}, "
                      f"Status={status['status']}")
                
                if status["status"] in ["completed", "failed", "cancelled"]:
                    break
                    
                time.sleep(2)
            
            # Step 5: Get call results
            print("\n5. Getting call results...")
            calls = client.batch_calling.get_job_calls(job_id)
            for call in calls.get("calls", []):
                print(f"   {call.get('to_number')}: {call.get('status')}")
            
            # Step 6: Cleanup
            print("\n6. Cleanup...")
            client.batch_calling.cancel_job(job_id)
            client.agents.delete_agent(agent_id)
            print("   Campaign cleanup completed")
            
        except ElevenLabsError as e:
            print(f"\nError: {e}")


def quick_start():
    """
    Minimal quick start example.
    """
    load_dotenv()
    
    print("\n" + "=" * 60)
    print("QUICK START")
    print("=" * 60)
    
    with ElevenLabsClient() as client:
        # Create agent
        agent = client.create_agent(
            name="Quick Agent",
            voice_id="21m00Tcm4TlvDq8ikWAM",
            first_message="Hello!"
        )
        print(f"Agent: {agent['agent_id']}")
        
        # Get agent
        info = client.get_agent(agent["agent_id"])
        print(f"Name: {info.get('name')}")
        
        # Delete agent
        client.delete_agent(agent["agent_id"])
        print("Deleted!")


if __name__ == "__main__":
    # Run examples
    print("\n" + "#" * 70)
    print("#  ELEVENLABS CLIENT EXAMPLES")
    print("#" * 70)
    
    # Choose which example to run
    # quick_start()
    unified_client_example()
    # individual_services_example()
    # batch_campaign_workflow()
