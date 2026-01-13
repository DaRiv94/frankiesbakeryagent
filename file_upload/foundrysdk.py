# Before running the sample:
#    pip install --pre azure-ai-projects>=2.0.0b1
#    pip install azure-identity

# Requries Azure CLI login forDefaultAzureCredential to work in local dev environment

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

myEndpoint = "https://proj-ais-eastus2-azure-foundry-t.services.ai.azure.com/api/projects/proj-ais-eastus2-azure-foundry-test"

project_client = AIProjectClient(
    endpoint=myEndpoint,
    credential=DefaultAzureCredential(),
)

myAgent = "2026-1-12-KnowledgeAgentTest02"
# Get an existing agent
agent = project_client.agents.get(agent_name=myAgent)
print(f"Retrieved agent: {agent.name}")

openai_client = project_client.get_openai_client()

# Reference the agent to get a response
response = openai_client.responses.create(
    input=[{"role": "user", "content": "Tell me what you can help with."}],
    extra_body={"agent": {"name": agent.name, "type": "agent_reference"}},
)

# # Reference the agent to get a response
# response = openai_client.responses.create(
#     input=[{"role": "user", "content": "I want to send some homemade-style chocolate chip cookies to a friend in another state as a gift. Can you tell me what's in them, how they should be stored when they arrive, how long shipping takes, whether they can be frozen for longer storage, and what your freshness guarantee covers?"}],
#     extra_body={"agent": {"name": agent.name, "type": "agent_reference"}},
# )


print(f"Response output: {response.output_text}")

