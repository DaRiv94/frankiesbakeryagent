
#Look at these
#https://github.com/microsoft/agent-framework/blob/main/python/samples/getting_started/agents/azure_ai/README.md

import asyncio
from agent_framework import ChatAgent
from agent_framework.azure import AzureAIAgentClient
from azure.identity.aio import DefaultAzureCredential
# from azure.identity.aio import AzureCliCredential

PROJECT_ENDPOINT = "https://proj-ais-eastus2-azure-foundry-t.services.ai.azure.com/api/projects/proj-ais-eastus2-azure-foundry-test"
MODEL_DEPLOYMENT_NAME = "gpt-5-mini"
credential = DefaultAzureCredential()

async def main():
    async with (
        ChatAgent(
            chat_client=AzureAIAgentClient(
                model_deployment_name=MODEL_DEPLOYMENT_NAME,
                project_endpoint=PROJECT_ENDPOINT,
                credential=credential,
                agent_id="2026-1-12-KnowledgeAgentTest02"
            ),
            instructions="You are a helpful assistant."
        ) as agent,
    ):
        result = await agent.run("Hello!")
        print(result.text)

asyncio.run(main())