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

myAgent = "2026-1-13-ActionAgent01"
# Get an existing agent
agent = project_client.agents.get(agent_name=myAgent)
print(f"Retrieved agent: {agent.name}")

openai_client = project_client.get_openai_client()

# Reference the agent to get a response
response = openai_client.responses.create(
    input=[{"role": "user", "content": "Who won the Citrus Bowl in 2025? What was the score? "}],  #ANSWER: The Texas Longhorns won the 2025 Citrus Bowl, defeating the Michigan Wolverines with a final score of 41-27 on December 31st 2025
    extra_body={"agent": {"name": agent.name, "type": "agent_reference"}},
)


print(f"Response output: {response.output_text}")