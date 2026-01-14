# Before running the sample:
#    pip install --pre azure-ai-projects>=2.0.0b1
#    pip install azure-identity

# Requires Azure CLI login for DefaultAzureCredential to work in local dev environment

import os
import time
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

myEndpoint = "https://proj-ais-eastus2-azure-foundry-t.services.ai.azure.com/api/projects/proj-ais-eastus2-azure-foundry-test"

project_client = AIProjectClient(
    endpoint=myEndpoint,
    credential=DefaultAzureCredential(),
)

myAgent = "2026-1-9-KnowledgeAgentTest01"

# Get an existing agent
agent = project_client.agents.get(agent_name=myAgent)
print(f"Retrieved agent: {agent.name}")

openai_client = project_client.get_openai_client()


def create_response_with_mcp_approval(conversation_id: str, agent_name: str, openai_client) -> str:
    """Create a response from the agent, handling MCP approval requests as needed."""
    response = openai_client.responses.create(
        conversation=conversation_id,
        extra_body={"agent": {"name": agent_name, "type": "agent_reference"}},
        input="",
    )
    
    # Check if response contains MCP approval requests
    while hasattr(response, 'output') and response.output:
        has_approval_request = False
        approval_responses = []
        
        for output_item in response.output:
            # Check for MCP approval requests
            if hasattr(output_item, 'type') and output_item.type == 'mcp_approval_request':
                has_approval_request = True

                print(f"MCP approval request detected: {output_item.arguments}")
                
                # Approve the MCP request
                approval_responses.append({
                    "type": "mcp_approval_response",
                    "approval_request_id": output_item.id,
                    "approve": True,
                })
        
        # If we had approval requests, submit the approvals and retry
        if has_approval_request:
            print(f"Submitting {len(approval_responses)} MCP approval(s)...")
            
            print(approval_responses)
            # Add approvals to conversation
            openai_client.conversations.items.create(
                conversation_id=conversation_id,
                items=approval_responses,
            )
            
            # Retry the response creation
            time.sleep(1)
            response = openai_client.responses.create(
                conversation=conversation_id,
                extra_body={"agent": {"name": agent_name, "type": "agent_reference"}},
                input="",
            )
        else:
            # No more approval requests, exit the loop
            break
    
    return response.output_text if hasattr(response, 'output_text') else str(response.output)


# Create a conversation
conversation = openai_client.conversations.create(
    items=[{"type": "message", "role": "user", "content": "Tell me what you can help with."}]
)
print(f"Created conversation (id: {conversation.id})")

# Use the agent to generate a response (with MCP approval handling)
response_text = create_response_with_mcp_approval(conversation.id, agent.name, openai_client)
print(f"Response output: {response_text}")

# # Add a follow-up message and continue the conversation
# openai_client.conversations.items.create(
#     conversation_id=conversation.id,
#     items=[{"type": "message", "role": "user", "content": "What bakery products do you have information about?"}],
# )

# # Get follow-up response (with MCP approval handling)
# response_text2 = create_response_with_mcp_approval(conversation.id, agent.name, openai_client)
# print(f"Follow-up response: {response_text2}")

# Clean up: delete the conversation
openai_client.conversations.delete(conversation_id=conversation.id)
print("Conversation deleted")