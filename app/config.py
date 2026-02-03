import os
from dotenv import load_dotenv
from cryptography.fernet import Fernet

load_dotenv(override=True)

def load_neo4j_credentials(path: str) -> dict:
    creds = {}

    with open(path, "r") as f:
        for line in f:
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith("#"):
                continue

            if "=" not in line:
                continue

            key, value = line.split("=", 1)
            creds[key.strip()] = value.strip()

    return creds


# Load credentials
neo4j_creds = load_neo4j_credentials(os.getenv("NEO4J_CREDS_FILE"))

NEO4J_URI = neo4j_creds["NEO4J_URI"]
NEO4J_USER = neo4j_creds["NEO4J_USERNAME"]
NEO4J_PASSWORD = neo4j_creds["NEO4J_PASSWORD"]
NEO4J_DATABASE = neo4j_creds.get("NEO4J_DATABASE", "neo4j")


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

FAISS_INDEX_PATH = "./data/faiss.index"
METADATA_PATH = "./data/metadata.pkl"
