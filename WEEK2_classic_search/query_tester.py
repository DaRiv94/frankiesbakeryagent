
import os
import argparse
from typing import Iterable, List

from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from openai import AzureOpenAI

# Load env vars from .env if present
load_dotenv()

DEFAULT_INDEX_NAME = "frankiesbakery02-classic-search-idx"
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-large"
DEFAULT_K = 5
DEFAULT_VECTOR_FIELD = "text_vector"  # change this if your index uses a different name

def require_setting(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Environment variable {name} is required")
    return value

def build_search_client(index_name: str) -> SearchClient:
    endpoint = require_setting("AZURE_SEARCH_SERVICE")
    key = require_setting("AZURE_SEARCH_KEY")
    return SearchClient(endpoint=endpoint, index_name=index_name, credential=AzureKeyCredential(key))

def build_openai_client() -> AzureOpenAI:
    endpoint = require_setting("AZURE_OPENAI_ACCOUNT")
    key = require_setting("AZURE_OPENAI_KEY")
    # Update api_version if your resource requires a different preview/GA
    return AzureOpenAI(api_key=key, azure_endpoint=endpoint, api_version="2024-02-15-preview")

def embed_text(text: str, model: str) -> List[float]:
    client = build_openai_client()
    result = client.embeddings.create(model=model, input=text)
    return result.data[0].embedding

def print_hits(hits: Iterable) -> None:
    for hit in hits:
        doc = hit.copy()
        score = doc.pop("@search.score", None)
        print("---")
        print(f"score={score}")
        for field, value in doc.items():
            print(f"{field}: {value}")

def run_vector_search(search_client: SearchClient, query: str, k: int, model: str, vector_field: str) -> None:
    # 1) Embed the query
    embedding = embed_text(query, model=model)

    # 2) Build the simple VectorizedQuery
    vq = VectorizedQuery(
        vector=embedding,
        k_nearest_neighbors=k,
        fields=vector_field,
    )

    # 3) Execute pure vector search
    results = search_client.search(
        search_text=None,
        vector_queries=[vq],
        select=["chunk_id", "title", "chunk", "parent_id"],
        top=k,  # optional
    )
    print_hits(results)


# Usage Examples:
# ---------------
# Basic vector search with 5 results (default):
#   python query_tester.py "banana bread recipe"
#
# Search with custom number of results:
#   python query_tester.py "chocolate chip cookies" --k 10
#
# Override index name:
#   python query_tester.py "sourdough starter tips" --index-name my-custom-index
#
# Override vector field name (Only if you have multiple vector fields in your index):
#   python query_tester.py "pizza dough" --vector-field my_vector_field


def main() -> None:
    parser = argparse.ArgumentParser(description="Simple vector query against an Azure AI Search index")
    parser.add_argument("query", help="User query text")
    parser.add_argument("--index-name", default=os.getenv("AZURE_SEARCH_INDEX_NAME", DEFAULT_INDEX_NAME), help="Target index name")
    parser.add_argument("--k", type=int, default=DEFAULT_K, help="Number of nearest neighbors to return")
    parser.add_argument("--vector-field", default=os.getenv("AZURE_SEARCH_VECTOR_FIELD", DEFAULT_VECTOR_FIELD), help="Vector field name in your index")
    args = parser.parse_args()

    client = build_search_client(args.index_name)
    run_vector_search(client, query=args.query, k=args.k, model=DEFAULT_EMBEDDING_MODEL, vector_field=args.vector_field)

if __name__ == "__main__":
    main()
