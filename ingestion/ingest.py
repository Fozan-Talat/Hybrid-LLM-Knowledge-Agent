from app.language import detect_language
from ingestion.ocr import ocr_pdf_with_azure
from ingestion.chunking import chunk_pages
from ingestion.embeddings import embed_texts
from ingestion.dedup import document_hash
from vectorstore.faiss_store import FaissStore
from graph.neo4j_client import Neo4jClient
from graph.graph_builder import extract_entities_smart, persist_chunks_batch

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

def is_valid_entity(entity: dict) -> bool:
    name = entity["name"].strip().lower()

    if len(name) < 4:
        return False

    if any(k in name for k in SIGNAL_KEYWORDS):
        return False

    if name.isnumeric():
        return False

    return True

def faiss_document_exists(doc_id: str) -> bool:
    store = FaissStore()
    try:
        store.load()
    except Exception:
        return False

    return any(
        meta.get("document_id") == doc_id
        for meta in store.metadata
    )

def ingest(pdf_path: str, force: bool = False) -> dict:
    doc_id = document_hash(pdf_path)
    faiss_exists = faiss_document_exists(doc_id)

    # 1. OCR
    pages = ocr_pdf_with_azure(pdf_path)
    if not pages:
        raise RuntimeError("OCR produced no text")

    # 2. Chunking
    chunks = chunk_pages(doc_id, pages)
    if not chunks:
        raise RuntimeError("No chunks generated")

    for chunk in chunks:
        lang = detect_language(chunk["text"])
        chunk["language"] = lang

    # 3. Embeddings (batched, deterministic order)
    texts = [c["text"] for c in chunks]
    vectors = embed_texts(texts)

    if not force and faiss_exists:
        return {
            "status": "skipped",
            "reason": "document already ingested",
            "document_id": doc_id
        }

    # 4. Vector store
    store = FaissStore()
    try:
        store.load()
    except Exception:
        pass

    store.add(vectors, chunks)
    store.save()

    # 5. Graph ingestion (BATCHED)
    graph = Neo4jClient()
    
    if not force and graph.document_exists(doc_id):
        return {
            "status": "skipped",
            "reason": "document already ingested",
            "document_id": doc_id
        }
    
    graph_payload = []
    for chunk in chunks:
        raw_entities = extract_entities_smart(chunk["text"], lang)

        entities = [
            e for e in raw_entities
            if is_valid_entity(e)
        ]

        if not entities:
            continue

        graph_payload.append({
            "chunk": chunk,
            "entities": entities
        })

    if graph_payload:
        with graph.driver.session() as session:
            session.execute_write(persist_chunks_batch, graph_payload)

    return {
        "status": "success",
        "document_id": doc_id,
        "pages": len(pages),
        "chunks": len(chunks),
        "entities_created": sum(len(p["entities"]) for p in graph_payload)
    }
