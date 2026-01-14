# Before running the sample:
#    pip install --pre azure-ai-projects>=2.0.0b1
#    pip install azure-identity

# Requries Azure CLI login forDefaultAzureCredential to work in local dev environment


# pip install azure-ai-projects --pre
# pip install openai azure-identity python-dotenv

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

myEndpoint = "https://proj-ais-eastus2-azure-foundry-t.services.ai.azure.com/api/projects/proj-ais-eastus2-azure-foundry-test"

project_client = AIProjectClient(
    endpoint=myEndpoint,
    credential=DefaultAzureCredential(),
)

myAgent = "2026-1-14-CodeAgent01"
# Get an existing agent
agent = project_client.agents.get(agent_name=myAgent)
print(f"Retrieved agent: {agent.name}")

openai_client = project_client.get_openai_client()

# Reference the agent to get a response
response = openai_client.responses.create(
    input=[{"role": "user", "content": "Give me a summary of the cost of all these bills using a Python program. 12/18/2026  $142.67 11/19/2026  $128.45 10/20/2026  $119.32 09/18/2026  $246.91 08/21/2026  $351.84 07/20/2026  $289.76 06/18/2026  $164.28 05/21/2026  $132.94 04/20/2026  $121.53 03/19/2026  $138.66 02/18/2026  $156.72 01/16/2026  $149.38"}],
    extra_body={"agent": {"name": agent.name, "type": "agent_reference"}},
)
# # Reference the agent to get a response
# response = openai_client.responses.create(
#     input=[{"role": "user", "content": "Please create a bar chart that shows the sales of each of my Frankies Bakery products."}],
#     extra_body={"agent": {"name": agent.name, "type": "agent_reference"}},
# )


print(f"Response output: {response.output_text}")