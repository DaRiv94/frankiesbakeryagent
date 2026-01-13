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
index_name_recipes = "frankies-bakery-recipes-index"
index_name_faq = "frankies-bakery-faq-index"
index_name_policies = "frankies-bakery-policies-index"
knowledge_source_name_recipes = "frankies-bakery-recipes-source"
knowledge_source_name_faq = "frankies-bakery-faq-source"
knowledge_source_name_policies = "frankies-bakery-policies-source"
knowledge_base_name = "frankies-bakery-knowledge-base"
search_api_version = "2025-11-01-preview"

credential = DefaultAzureCredential()
token_provider = get_bearer_token_provider(credential, "https://search.azure.com/.default")

# Create indexes
azure_openai_token_provider = get_bearer_token_provider(credential, "https://cognitiveservices.azure.com/.default")

# Common index configuration
def create_index_config(index_name):
    return SearchIndex(
        name=index_name,
        fields=[
            SearchField(name="id", type="Edm.String", key=True, filterable=True, sortable=True, facetable=True),
            SearchField(name="page_chunk", type="Edm.String", filterable=False, sortable=False, facetable=False),
            SearchField(name="page_embedding_text_3_large", type="Collection(Edm.Single)", stored=False, vector_search_dimensions=3072, vector_search_profile_name="hnsw_text_3_large"),
            SearchField(name="page_number", type="Edm.Int32", filterable=True, sortable=True, facetable=True)
        ],
        vector_search=VectorSearch(
            profiles=[VectorSearchProfile(name="hnsw_text_3_large", algorithm_configuration_name="alg", vectorizer_name="azure_openai_text_3_large")],
            algorithms=[HnswAlgorithmConfiguration(name="alg")],
            vectorizers=[
                AzureOpenAIVectorizer(
                    vectorizer_name="azure_openai_text_3_large",
                    parameters=AzureOpenAIVectorizerParameters(
                        resource_url=aoai_endpoint,
                        deployment_name=aoai_embedding_deployment,
                        model_name=aoai_embedding_model
                    )
                )
            ]
        ),
        semantic_search=SemanticSearch(
            default_configuration_name="semantic_config",
            configurations=[
                SemanticConfiguration(
                    name="semantic_config",
                    prioritized_fields=SemanticPrioritizedFields(
                        content_fields=[
                            SemanticField(field_name="page_chunk")
                        ]
                    )
                )
            ]
        )
    )

index_client = SearchIndexClient(endpoint=search_endpoint, credential=credential)

# Create all three indexes
recipes_index = create_index_config(index_name_recipes)
index_client.create_or_update_index(recipes_index)
print(f"Index '{index_name_recipes}' created or updated successfully.")

faq_index = create_index_config(index_name_faq)
index_client.create_or_update_index(faq_index)
print(f"Index '{index_name_faq}' created or updated successfully.")

policies_index = create_index_config(index_name_policies)
index_client.create_or_update_index(policies_index)
print(f"Index '{index_name_policies}' created or updated successfully.")

# Fetch all data sources
url_recipes = "https://raw.githubusercontent.com/DaRiv94/frankiesbakeryagent/refs/heads/master/Recipes.json"
raw_recipes = requests.get(url_recipes).json()

url_faq = "https://raw.githubusercontent.com/DaRiv94/frankiesbakeryagent/refs/heads/master/faq.json"
raw_faq = requests.get(url_faq).json()

url_policies = "https://raw.githubusercontent.com/DaRiv94/frankiesbakeryagent/refs/heads/master/Policyinfo.json"
raw_policies = requests.get(url_policies).json()

# Transform and upload recipes
recipes_documents = []
for idx, recipe in enumerate(raw_recipes, start=1):
    ingredients_text = "\n".join(f"  - {ing}" for ing in recipe.get('ingredients', []))
    page_chunk = f"""# {recipe.get('recipe_name', 'Untitled Recipe')}

{recipe.get('description', '')}

## Ingredients
{ingredients_text}

## Instructions
{recipe.get('instructions', '')}

## Storage Tips
{recipe.get('storage_tips', '')}

## Source
{recipe.get('source', '')}"""
    
    recipes_documents.append({
        'id': recipe['id'],
        'page_chunk': page_chunk,
        'page_number': idx
    })

with SearchIndexingBufferedSender(endpoint=search_endpoint, index_name=index_name_recipes, credential=credential) as client:
    client.upload_documents(documents=recipes_documents)
print(f"Documents uploaded to index '{index_name_recipes}' successfully.")

# Transform and upload FAQ
faq_documents = []
for idx, faq in enumerate(raw_faq, start=1):
    page_chunk = f"""# {faq.get('question', 'Untitled Question')}

{faq.get('answer', '')}"""
    
    faq_documents.append({
        'id': faq['id'],
        'page_chunk': page_chunk,
        'page_number': idx
    })

with SearchIndexingBufferedSender(endpoint=search_endpoint, index_name=index_name_faq, credential=credential) as client:
    client.upload_documents(documents=faq_documents)
print(f"Documents uploaded to index '{index_name_faq}' successfully.")

# Transform and upload policies
policies_documents = []
for idx, policy in enumerate(raw_policies, start=1):
    page_chunk = f"""# {policy.get('policy_name', 'Untitled Policy')}

{policy.get('content', '')}"""
    
    policies_documents.append({
        'id': policy['id'],
        'page_chunk': page_chunk,
        'page_number': idx
    })

with SearchIndexingBufferedSender(endpoint=search_endpoint, index_name=index_name_policies, credential=credential) as client:
    client.upload_documents(documents=policies_documents)
print(f"Documents uploaded to index '{index_name_policies}' successfully.")

# Create three knowledge sources
index_client = SearchIndexClient(endpoint=search_endpoint, credential=credential)

ks_recipes = SearchIndexKnowledgeSource(
    name=knowledge_source_name_recipes,
    description="Knowledge source for Frankie's Bakery recipes",
    search_index_parameters=SearchIndexKnowledgeSourceParameters(
        search_index_name=index_name_recipes,
        source_data_fields=[SearchIndexFieldReference(name="id"), SearchIndexFieldReference(name="page_number")]
    ),
)
index_client.create_or_update_knowledge_source(knowledge_source=ks_recipes)
print(f"Knowledge source '{knowledge_source_name_recipes}' created or updated successfully.")

ks_faq = SearchIndexKnowledgeSource(
    name=knowledge_source_name_faq,
    description="Knowledge source for Frankie's Bakery FAQ",
    search_index_parameters=SearchIndexKnowledgeSourceParameters(
        search_index_name=index_name_faq,
        source_data_fields=[SearchIndexFieldReference(name="id"), SearchIndexFieldReference(name="page_number")]
    ),
)
index_client.create_or_update_knowledge_source(knowledge_source=ks_faq)
print(f"Knowledge source '{knowledge_source_name_faq}' created or updated successfully.")

ks_policies = SearchIndexKnowledgeSource(
    name=knowledge_source_name_policies,
    description="Knowledge source for Frankie's Bakery policies",
    search_index_parameters=SearchIndexKnowledgeSourceParameters(
        search_index_name=index_name_policies,
        source_data_fields=[SearchIndexFieldReference(name="id"), SearchIndexFieldReference(name="page_number")]
    ),
)
index_client.create_or_update_knowledge_source(knowledge_source=ks_policies)
print(f"Knowledge source '{knowledge_source_name_policies}' created or updated successfully.")

# Create a knowledge base
aoai_params = AzureOpenAIVectorizerParameters(
    resource_url=aoai_endpoint,
    deployment_name=aoai_gpt_deployment,
    model_name=aoai_gpt_model,
)

knowledge_base = KnowledgeBase(
    name=knowledge_base_name,
    models=[KnowledgeBaseAzureOpenAIModel(azure_open_ai_parameters=aoai_params)],
    knowledge_sources=[
        KnowledgeSourceReference(name=knowledge_source_name_recipes),
        KnowledgeSourceReference(name=knowledge_source_name_faq),
        KnowledgeSourceReference(name=knowledge_source_name_policies)
    ],
    output_mode=KnowledgeRetrievalOutputMode.ANSWER_SYNTHESIS,
    answer_instructions="Provide a two sentence concise and informative answer based on the retrieved documents."
)

index_client = SearchIndexClient(endpoint=search_endpoint, credential=credential)
index_client.create_or_update_knowledge_base(knowledge_base)
print(f"Knowledge base '{knowledge_base_name}' created or updated successfully.")