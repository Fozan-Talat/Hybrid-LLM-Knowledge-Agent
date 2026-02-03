import re
import spacy
from openai import OpenAI
import json

client = OpenAI()

nlp = spacy.load("en_core_web_sm")

SIGNAL_KEYWORDS = {
    "velocity",
    "length",
    "length error",
    "force",
    "feedback",
    "bias",
    "signal",
    "control",
    "error"
}

VALID_ENTITY_LABELS = {
    "ORG",
    "PERSON",
    "PRODUCT",
    "GPE",
    "LOC",
    "EVENT",
    "WORK_OF_ART",
    "LAW",
    "LANGUAGE"
}


def normalize_entity(text: str) -> str:
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    return text


def is_valid_entity(text: str, label: str) -> bool:
    t = text.lower()

    if len(t) < 4:
        return False

    if any(k in t for k in SIGNAL_KEYWORDS):
        return False

    if t.isnumeric():
        return False

    # allow unknown labels, but block obviously bad ones
    if label in {"CARDINAL", "ORDINAL", "QUANTITY", "PERCENT"}:
        return False

    return True


def extract_entities_llm(text: str, lang: str) -> list[dict]:
    """
    Multilingual entity extraction using LLM.
    Works especially well for Arabic.
    Returns the SAME entity schema used elsewhere.
    """

    prompt = f"""
You are a named entity extraction system.

Extract meaningful named entities from the following text.
Entities should be real-world concepts such as:
- people
- organizations
- places
- products
- laws
- languages
- events

Rules:
- Ignore generic words and abstract concepts
- Ignore numbers and measurements
- Do NOT hallucinate entities
- Preserve original language (do NOT translate)

Return ONLY valid JSON in the following format:
[
  {{
    "name": "<entity text>",
    "entity_type": "<person|organization|location|product|event|law|language|other>"
  }}
]

Text language: {lang}

Text:
\"\"\"{text}\"\"\"
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        content = response.choices[0].message.content.strip()

        # Defensive cleanup (LLMs sometimes wrap JSON)
        content = re.sub(r"^```json|```$", "", content, flags=re.MULTILINE).strip()

        entities = json.loads(content)

        # Normalize to your existing schema
        normalized = []
        for e in entities:
            if not e.get("name"):
                continue

            normalized.append({
                "name": e["name"].strip(),
                "entity_type": e.get("entity_type", "unknown"),
                "source_label": "LLM",
                "language": lang
            })

        return normalized

    except Exception as e:
        print("LLM entity extraction failed:", e)
        return []
    
def extract_entities_smart(text: str, lang: str) -> list[dict]:
    """
    Automatically selects the best entity extractor
    based on detected language.
    """

    # English → spaCy (fast, cheap)
    if lang == "en":
        return extract_entities(text)

    # Arabic & everything else → LLM
    return extract_entities_llm(text, lang)

def extract_entities(text: str):
    # nlp = get_nlp()
    print(nlp.pipe_names)
    doc = nlp(text)
    print(doc.ents)
    print([(e.text, e.label_) for e in doc.ents])

    # doc = nlp("Apple was founded by Steve Jobs in California.")
    # print([(e.text, e.label_) for e in doc.ents])

    entities = {}
    for ent in doc.ents:
        name = normalize_entity(ent.text)

        if not is_valid_entity(name, ent.label_):
            continue

        # de-duplicate within chunk
        entities[name.lower()] = {
            "name": name,
            "entity_type": "unknown",   # evolve later
            "source_label": ent.label_
        }

    return list(entities.values())

def persist_chunk(tx, chunk, entities):
    tx.run(
        """
        MERGE (d:Document {id: $doc_id})
        MERGE (c:Chunk {id: $chunk_id})
        SET c.text = $text,
            c.page = $page
        MERGE (d)-[:CONTAINS]->(c)

        WITH c
        UNWIND $entities AS ent
        MERGE (e:Entity {name: ent.name})
        SET e.entity_type = ent.entity_type
        MERGE (c)-[:MENTIONS]->(e)
        """,
        {
            "doc_id": chunk["document_id"],
            "chunk_id": chunk["chunk_id"],
            "text": chunk["text"],
            "page": chunk["page_number"],
            "entities": entities
        }
    )

def persist_chunks_batch(tx, payload):
    tx.run(
        """
        UNWIND $payload AS row
        MERGE (d:Document {id: row.chunk.document_id})
        MERGE (c:Chunk {id: row.chunk.chunk_id})
        SET c.text = row.chunk.text,
            c.page = row.chunk.page_number
        MERGE (d)-[:CONTAINS]->(c)

        WITH c, row.entities AS entities
        UNWIND entities AS ent
        MERGE (e:Entity {name: ent.name})
        SET e.entity_type = ent.entity_type
        MERGE (c)-[:MENTIONS]->(e)
        """,
        payload=payload
    )
