from neo4j import GraphDatabase
from app.config import *

class Neo4jClient:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD)
        )

    def run(self, query, params=None):
        with self.driver.session() as session:
            return list(session.run(query, params or {}))

    def document_exists(self, doc_id: str) -> bool:
        with self.driver.session() as session:
            result = session.run(
                "MATCH (d:Document {id: $id}) RETURN d LIMIT 1",
                {"id": doc_id}
            )
            return result.single() is not None