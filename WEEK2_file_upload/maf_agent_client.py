
#Look at these
#https://github.com/microsoft/agent-framework/blob/main/python/samples/getting_started/agents/azure_ai/README.md

import asyncio
from agent_framework import ChatAgent
from agent_framework.azure import AzureAIAgentClient
from azure.identity.aio import DefaultAzureCredential

PROJECT_ENDPOINT = "https://proj-ais-eastus2-azure-foundry-t.services.ai.azure.com/api/projects/proj-ais-eastus2-azure-foundry-test"
MODEL_NAME = "gpt-5-mini"

async def main():
    credential = DefaultAzureCredential()
    async with ChatAgent(
        chat_client=AzureAIAgentClient(
            project_endpoint=PROJECT_ENDPOINT,
            model_deployment_name=MODEL_NAME,
            async_credential=credential,
            agent_id="2026-1-12-KnowledgeAgentTest02"
        )
    ) as agent:
        result = await agent.run("Hello what can you do?")
        print(result.text)
    await credential.close()

asyncio.run(main())
# async def main():
#     async with (
#         AzureCliCredential() as credential,
#         ChatAgent(
#             chat_client=AzureAIAgentClient(
#                 project_endpoint=PROJECT_ENDPOINT,
#                 model_deployment_name=MODEL_NAME,
#                 async_credential=credential,
#                 agent_id="<existing-agent-id>"
#             ),
#             instructions="You are a helpful assistant."
#         ) as agent,
#     ):
#         result = await agent.run("Hello!")
#         print(result.text)

# asyncio.run(main())