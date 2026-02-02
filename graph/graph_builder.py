import re
import spacy
import stanza

# stanza.download('en', package='mimic', processors={'ner': 'i2b2'})         

nlp = spacy.load("en_core_web_sm")
# nlp = stanza.Pipeline('en', package='mimic', processors={'ner': 'i2b2'})
# _nlp = None

def get_nlp():
    global _nlp
    if _nlp is None:
        _nlp = stanza.Pipeline(
            lang="en",
            processors="tokenize,pos,lemma,depparse,ner",
            package=None,
            ner_package="i2b2",
            use_gpu=False
        )
    return _nlp

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
