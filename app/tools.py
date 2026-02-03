from app.config import SERPAPI_KEY
from vectorstore.faiss_store import FaissStore
from ingestion.embeddings import embed_texts
from graph.neo4j_client import Neo4jClient
import requests

def vector_search(query: str, query_lang: str):
    store = FaissStore()
    store.load()
    qvec = embed_texts([query])[0]
    results = store.search(qvec)
    # return [r for r in results if r.get("language") == query_lang]
    return [r for r in results]

def graph_search(entity_name: str):
    graph = Neo4jClient()
    return graph.run("""
        MATCH (e:Entity {name: $name})<-[:MENTIONS]-(c:Chunk)
        MATCH (d:Document)-[:CONTAINS]->(c)
        RETURN
            d.id    AS document_id,
            c.id    AS chunk_id,
            c.text  AS text,
            c.page  AS page_number
    """, {"name": entity_name})

def online_search(query: str):
    return requests.get(
        "https://serpapi.com/search",
        params={"q": query, "api_key": SERPAPI_KEY}
    ).json()
