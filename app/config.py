import os
from dotenv import load_dotenv

load_dotenv(override=True)

from cryptography.fernet import Fernet
import os

FERNET_KEY = os.getenv("FERNET_KEY")  # or from secure store
cipher = Fernet(FERNET_KEY.encode())

with open(".env.enc", "rb") as f:
    decrypted = cipher.decrypt(f.read()).decode()

for line in decrypted.splitlines():
    if line and not line.startswith("#"):
        key, value = line.split("=", 1)
        os.environ[key] = value

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
AZURE_DOCUMENT_INTELLIGENCE_KEY = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

FAISS_INDEX_PATH = "./data/faiss.index"
METADATA_PATH = "./data/metadata.pkl"
