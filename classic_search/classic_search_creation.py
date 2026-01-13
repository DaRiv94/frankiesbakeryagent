import os
from azure.identity import get_bearer_token_provider
from azure.search.documents.indexes import SearchIndexClient, SearchIndexerClient
from azure.search.documents.indexes.models import (
     SearchField,
     SearchFieldDataType,
     VectorSearch,
     HnswAlgorithmConfiguration,
     HnswParameters,
     VectorSearchProfile,
     AzureOpenAIVectorizer,
     AzureOpenAIVectorizerParameters,
     SearchIndex,
     SearchIndexerDataContainer,
     SearchIndexerDataSourceConnection,
     SplitSkill,
     InputFieldMappingEntry,
     OutputFieldMappingEntry,
     AzureOpenAIEmbeddingSkill,
     EntityRecognitionSkill,
     SearchIndexerIndexProjection,
     SearchIndexerIndexProjectionSelector,
     SearchIndexerIndexProjectionsParameters,
     IndexProjectionMode,
     SearchIndexerSkillset,
     CognitiveServicesAccountKey,
     SearchIndexer,
     SemanticConfiguration,
     SemanticPrioritizedFields,
     SemanticField,
     SemanticSearch
 )



from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()

AZURE_SEARCH_SERVICE=os.getenv("AZURE_SEARCH_SERVICE")
AZURE_SEARCH_KEY=os.getenv("AZURE_SEARCH_KEY")
AZURE_OPENAI_ACCOUNT=os.getenv("AZURE_OPENAI_ACCOUNT")
AZURE_STORAGE_CONNECTION=os.getenv("AZURE_STORAGE_CONNECTION")
AZURE_OPENAI_KEY=os.getenv("AZURE_OPENAI_KEY")

# Create a credential object with the admin key
from azure.core.credentials import AzureKeyCredential
credential = AzureKeyCredential(AZURE_SEARCH_KEY)

prefix = "frankiesbakery02"
index_name = f"{prefix}-classic-search-idx"
data_source_name = f"{prefix}-classic-search-ds"
skillset_name = f"{prefix}-classic-search-ss"
indexer_name = f"{prefix}-classic-search-idxr"

embedding_model_deployment_name = "text-embedding-3-large"
embedding_model_name = "text-embedding-3-large"
HnswAlgorithmConfiguration_name = f"{index_name}-hnsw-algorithm"
my_vector_search_profile_name = f"{index_name}-aiFoundryCatalog-text-profile"
my_vectorizer_name = f"{index_name}-aiFoundryCatalog-text-vectorizer"
my_semantic_config_name = f"{index_name}-semantic-configuration"


index_description = "Index Description for Frankies Bakery Classic Search"
search_indexer_skillset_description = "Skillset description for Frankies Bakery Classic Search"
indexer_description="Indexer description for Frankies Bakery Classic Search"

storage_container_name="frankies-bakery-docs"

##################### CREATE SEARCH INDEX ########################################################################

 # Create a search index  
index_client = SearchIndexClient(endpoint=AZURE_SEARCH_SERVICE, credential=credential)  
fields = [
     SearchField(name="chunk_id", type=SearchFieldDataType.String, key=True, searchable=True, sortable=True, filterable=False, facetable=False, analyzer_name="keyword"),  
     SearchField(name="parent_id", type=SearchFieldDataType.String, searchable=False, filterable=True, facetable=False),  
     SearchField(name="chunk", type=SearchFieldDataType.String, searchable=True, filterable=False, facetable=False),  
     SearchField(name="title", type=SearchFieldDataType.String, searchable=True, filterable=False, facetable=False),  
     SearchField(name="text_vector", type=SearchFieldDataType.Collection(SearchFieldDataType.Single), searchable=True, hidden=False, vector_search_dimensions=3072, vector_search_profile_name=my_vector_search_profile_name)
     ]  

 # Configure the vector search configuration  
vector_search = VectorSearch(  
     algorithms=[  
         HnswAlgorithmConfiguration(
             name=HnswAlgorithmConfiguration_name,
             parameters=HnswParameters(
                 metric="cosine",
                 m=4,
                 ef_construction=400,
                 ef_search=500
             )
         ),
     ],  
     profiles=[  
         VectorSearchProfile(  
             name=my_vector_search_profile_name,  
             algorithm_configuration_name=HnswAlgorithmConfiguration_name,  
             vectorizer_name=my_vectorizer_name,  
         )
     ],  
     vectorizers=[  
         AzureOpenAIVectorizer(  
             vectorizer_name=my_vectorizer_name,  
             kind="azureOpenAI",  
             parameters=AzureOpenAIVectorizerParameters(  
                 resource_url=AZURE_OPENAI_ACCOUNT,  
                 deployment_name=embedding_model_deployment_name,
                 model_name=embedding_model_name
             ),
         ),  
     ], 
 )

# New semantic configuration
semantic_config = SemanticConfiguration(
    name=my_semantic_config_name,
    prioritized_fields=SemanticPrioritizedFields(
        title_field=SemanticField(field_name="title"),
        content_fields=[SemanticField(field_name="chunk")]
    )
)

# Create the semantic settings with the configuration
semantic_search = SemanticSearch(configurations=[semantic_config])  

 # Create the search index
index = SearchIndex(name=index_name, fields=fields, vector_search=vector_search, semantic_search=semantic_search, description=index_description)  
result = index_client.create_or_update_index(index)  
print(f"{result.name} created or updated")


##################### CREATE DATA SOURCE ########################################################################

# Create a data source 
indexer_client = SearchIndexerClient(endpoint=AZURE_SEARCH_SERVICE, credential=credential)
container = SearchIndexerDataContainer(name=storage_container_name)
data_source_connection = SearchIndexerDataSourceConnection(
    name=data_source_name,
    type="azureblob",
    connection_string=AZURE_STORAGE_CONNECTION,
    container=container
)
data_source = indexer_client.create_or_update_data_source_connection(data_source_connection)

print(f"Data source '{data_source.name}' created or updated")


##################### CREATE SKILLSET ########################################################################

# Create a skillset  

#SKILL 1 Split Skill
split_skill = SplitSkill(  
    description="Split skill to chunk documents",  
    text_split_mode="pages",  
    context="/document",  
    maximum_page_length=2000,  
    page_overlap_length=500,  
    inputs=[  
        InputFieldMappingEntry(name="text", source="/document/content"),  
    ],  
    outputs=[  
        OutputFieldMappingEntry(name="textItems", target_name="pages")  
    ],  
)  

#SKILL 2 Embedding Skill
embedding_skill = AzureOpenAIEmbeddingSkill(  
    description="Skill to generate embeddings via Azure OpenAI",  
    context="/document/pages/*",  
    resource_url=AZURE_OPENAI_ACCOUNT,  
    deployment_name=embedding_model_deployment_name,  
    model_name=embedding_model_name,
    dimensions=3072,
    inputs=[  
        InputFieldMappingEntry(name="text", source="/document/pages/*"),  
    ],  
    outputs=[  
        OutputFieldMappingEntry(name="embedding", target_name="text_vector")  
    ],  
)

  
index_projections = SearchIndexerIndexProjection(  
    selectors=[  
        SearchIndexerIndexProjectionSelector(  
            target_index_name=index_name,  
            parent_key_field_name="parent_id",  
            source_context="/document/pages/*",  
            mappings=[  
                InputFieldMappingEntry(name="chunk", source="/document/pages/*"),  
                InputFieldMappingEntry(name="text_vector", source="/document/pages/*/text_vector"),
                InputFieldMappingEntry(name="title", source="/document/metadata_storage_name"),  
            ],  
        ),  
    ],  
    parameters=SearchIndexerIndexProjectionsParameters(  
        projection_mode=IndexProjectionMode.SKIP_INDEXING_PARENT_DOCUMENTS  
    ),  
) 

cognitive_services_account = CognitiveServicesAccountKey(key=AZURE_OPENAI_KEY)

skills = [split_skill, embedding_skill]

skillset = SearchIndexerSkillset(  
    name=skillset_name,  
    description=search_indexer_skillset_description,  
    skills=skills,  
    index_projection=index_projections,
    cognitive_services_account=cognitive_services_account
)
  
client = SearchIndexerClient(endpoint=AZURE_SEARCH_SERVICE, credential=credential)  
client.create_or_update_skillset(skillset)  
print(f"{skillset.name} created")  




##################### CREATE SEARCH INDEXER ########################################################################

# Create an indexer  
indexer_parameters = None

indexer = SearchIndexer(  
    name=indexer_name,  
    description=indexer_description,  
    skillset_name=skillset_name,  
    target_index_name=index_name,  
    data_source_name=data_source_name,
    parameters=indexer_parameters
)  

# Create and run the indexer  
indexer_client = SearchIndexerClient(endpoint=AZURE_SEARCH_SERVICE, credential=credential)  
indexer_result = indexer_client.create_or_update_indexer(indexer)  

print(f'{indexer_name} is created and running. Give the indexer a few minutes before running a query.')  