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
