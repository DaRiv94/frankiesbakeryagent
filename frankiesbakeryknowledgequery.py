


from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure.search.documents.indexes.models import SearchIndex, SearchField, VectorSearch, VectorSearchProfile, HnswAlgorithmConfiguration, AzureOpenAIVectorizer, AzureOpenAIVectorizerParameters, SemanticSearch, SemanticConfiguration, SemanticPrioritizedFields, SemanticField, SearchIndexKnowledgeSource, SearchIndexKnowledgeSourceParameters, SearchIndexFieldReference, KnowledgeBase, KnowledgeBaseAzureOpenAIModel, KnowledgeSourceReference, KnowledgeRetrievalOutputMode, KnowledgeRetrievalLowReasoningEffort
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents import SearchIndexingBufferedSender
from azure.search.documents.knowledgebases import KnowledgeBaseRetrievalClient
from azure.search.documents.knowledgebases.models import KnowledgeBaseRetrievalRequest, KnowledgeBaseMessage, KnowledgeBaseMessageTextContent, SearchIndexKnowledgeSourceParams
import requests
import json

# Define variables
search_endpoint = "https://aisearch-ais-eastus2-msftfoundry-test.search.windows.net"
aoai_endpoint = "https://proj-ais-eastus2-azure-foundry-t.openai.azure.com/"
aoai_embedding_model = "text-embedding-3-large"
aoai_embedding_deployment = "text-embedding-3-large"
aoai_gpt_model = "gpt-5-mini"
aoai_gpt_deployment = "gpt-5-mini"
knowledge_source_name_recipes = "frankies-bakery-recipes-source"
knowledge_source_name_faq = "frankies-bakery-faq-source"
knowledge_source_name_policies = "frankies-bakery-policies-source"
knowledge_base_name = "frankies-bakery-knowledge-base"
search_api_version = "2025-11-01-preview"

credential = DefaultAzureCredential()



# Set up messages
instructions = """
You are our helpful assistant that must use the knowledge base to answer all the questions from user. You never answer from your own knowledge under any circumstances. If you do not find information from the knowledge base to answer the question, you say, "I don't know."  You never use your own knowledge instead.  Always list your references by giving the exact blob storage link in your response. 
"""

messages = [
    {
        "role": "system",
        "content": instructions
    }
]

# Run agentic retrieval
agent_client = KnowledgeBaseRetrievalClient(endpoint=search_endpoint, knowledge_base_name=knowledge_base_name, credential=credential)
query_1 = """
 "I want to send some homemade-style chocolate chip cookies to a friend in another state as a gift. Can you tell me what's in them, how they should be stored when they arrive, how long shipping takes, whether they can be frozen for longer storage, and what your freshness guarantee covers?"
    """

messages.append({
    "role": "user",
    "content": query_1
})

req = KnowledgeBaseRetrievalRequest(
    messages=[
        KnowledgeBaseMessage(
            role=m["role"],
            content=[KnowledgeBaseMessageTextContent(text=m["content"])]
        ) for m in messages if m["role"] != "system"
    ],
    knowledge_source_params=[
        SearchIndexKnowledgeSourceParams(
            knowledge_source_name=knowledge_source_name_recipes,
            include_references=True,
            include_reference_source_data=True,
            always_query_source=True
        ),
        SearchIndexKnowledgeSourceParams(
            knowledge_source_name=knowledge_source_name_faq,
            include_references=True,
            include_reference_source_data=True,
            always_query_source=True
        ),
        SearchIndexKnowledgeSourceParams(
            knowledge_source_name=knowledge_source_name_policies,
            include_references=True,
            include_reference_source_data=True,
            always_query_source=True
        )
    ],
    include_activity=True,
    retrieval_reasoning_effort=KnowledgeRetrievalLowReasoningEffort
)

print(f"Retrieving content from knowledge base '{knowledge_base_name}'...")

result = agent_client.retrieve(retrieval_request=req)
print(f"Retrieved content from '{knowledge_base_name}' successfully.")

# Display the response, activity, and references
response_contents = []
activity_contents = []
references_contents = []

response_parts = []
for resp in result.response:
    for content in resp.content:
        response_parts.append(content.text)
response_content = "\n\n".join(response_parts) if response_parts else "No response found on 'result'"

response_contents.append(response_content)

# Print the three string values
print("response_content:\n", response_content, "\n")

messages.append({
    "role": "assistant",
    "content": response_content
})

if result.activity:
    activity_content = json.dumps([a.as_dict() for a in result.activity], indent=2)
else:
    activity_content = "No activity found on 'result'"

activity_contents.append(activity_content)
print("activity_content:\n", activity_content, "\n")

if result.references:
    references_content = json.dumps([r.as_dict() for r in result.references], indent=2)
else:
    references_content = "No references found on 'result'"

references_contents.append(references_content)
print("references_content:\n", references_content)