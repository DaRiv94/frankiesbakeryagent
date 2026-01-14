import os
import httpx
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition, CodeInterpreterTool, CodeInterpreterToolAuto

load_dotenv()

# Load the CSV file to be processed
asset_file_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "./sales_and_reviews.csv")
)

project_client = AIProjectClient(
    endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
    credential=DefaultAzureCredential(),
)

with project_client:
    openai_client = project_client.get_openai_client()

    # Upload the CSV file for the code interpreter to use
    file = openai_client.files.create(purpose="assistants", file=open(asset_file_path, "rb"))
    print(f"File uploaded (id: {file.id})")

    # Create agent with code interpreter tool
    agent = project_client.agents.create_version(
        agent_name="2026-1-14-CodeAgent02-FromCode",
        definition=PromptAgentDefinition(
            model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
            instructions="You are a helpful assistant. That uses Code Interpreter",
            tools=[CodeInterpreterTool(container=CodeInterpreterToolAuto(file_ids=[file.id]))],
        ),
        description="Code interpreter agent for data analysis and visualization.",
    )
    print(f"Agent created (id: {agent.id}, name: {agent.name}, version: {agent.version})")

    # Create a conversation for the agent interaction
    conversation = openai_client.conversations.create()
    print(f"Created conversation (id: {conversation.id})")

    # Send request to create a chart and generate a file
    response = openai_client.responses.create(
        conversation=conversation.id,
        input="Please create a bar chart that show the overall total sales of each of my Frankies Bakery products. make each bar a different color. Save the chart as a PNG file.",
        extra_body={"agent": {"name": agent.name, "type": "agent_reference"}},
    )
    print(f"Response completed (id: {response.id})")

    # Extract file information from response annotations
    file_id = ""
    filename = ""
    container_id = ""

    # Get the last message which should contain file citations
    last_message = response.output[-1]  # ResponseOutputMessage
    if last_message.type == "message":
        # Get the last content item (contains the file annotations)
        text_content = last_message.content[-1]  # ResponseOutputText
        if text_content.type == "output_text":
            # Get the last annotation (most recent file)
            if text_content.annotations:
                file_citation = text_content.annotations[-1]  # AnnotationContainerFileCitation
                if file_citation.type == "container_file_citation":
                    file_id = file_citation.file_id
                    filename = file_citation.filename
                    container_id = file_citation.container_id
                    print(f"Found generated file: {filename} (ID: {file_id})")

    # Download the generated file if available
    if file_id and filename:
        file_content = openai_client.containers.files.content.retrieve(file_id=file_id, container_id=container_id)
        with open(filename, "wb") as f:
            f.write(file_content.read())
            print(f"File {filename} downloaded successfully.")
        print(f"File ready for download: {filename}")
    else:
        print("No file generated in response")
    #uncomment these lines if you want to delete your agent
    #print("\nCleaning up...")
    #project_client.agents.delete_version(agent_name=agent.name, agent_version=agent.version)
    #print("Agent deleted")