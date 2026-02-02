```markdown
# Hybrid LLM Knowledge Agent

## Overview

This project implements a **Hybrid LLM Knowledge Agent** that ingests **scanned (image-based) PDF documents**, builds a **hybrid knowledge base** (vector + graph), and answers user questions through a chat/API interface with **explicit provenance and traceability**.

The system prioritizes **internal knowledge** extracted from PDFs and **falls back to online search** only when internal information is insufficient.

---

## Key Features

- OCR of scanned PDFs using **Azure Document Intelligence**
- PDF ingestion via REST API
- Semantic retrieval using **FAISS** vector index
- Symbolic reasoning using **Neo4j** graph database
- Hybrid retrieval at query time (vector + graph)
- Tool-driven LLM agent orchestration
- Online search fallback using **SerpAPI**
- Page- and chunk-level citations for every answer
- Clear indication of knowledge source (internal / online / both)

---

## High-Level Architecture

```

User
↓
FastAPI (API / Chat Interface)
├── POST /ingest/pdf
└── POST /ask
↓
LLM Agent (Tool-Orchestrated)
├── Vector Search (FAISS)
├── Graph Queries (Neo4j)
└── Online Search (SerpAPI, fallback only)
↓
Answer + Provenance

````

---

## Prerequisites

- Docker
- Docker Compose
- Azure credentials configured locally
- API keys for:
  - OpenAI
  - SerpAPI

---

## Environment Variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=sk-xxxxxxxx
SERPAPI_KEY=xxxxxxxx
````

---

## Running the System

### Build and Start Services

```bash
docker compose up --build
```

This will start:

* **API Service**: [http://localhost:8000](http://localhost:8000)
* **Neo4j Browser**: [http://localhost:7474](http://localhost:7474)

  * Username: `neo4j`
  * Password: `password`

---

## PDF Ingestion API

### Endpoint

```
POST /ingest/pdf
```

### Request

* Content-Type: `multipart/form-data`
* Field name: `file`
* Supported format: PDF only
* Maximum size: **5 MB** (Azure Document Intelligence limit)

### Example

```bash
curl -X POST http://localhost:8000/ingest/pdf \
  -F "file=@sample_scanned.pdf"
```

### Example Response

```json
{
  "status": "success",
  "document_id": "a3c9f0d1...",
  "pages_ingested": 10,
  "chunks_created": 42
}
```

### Ingestion Steps

1. OCR extraction using Azure Document Intelligence
2. Text normalization and chunking
3. Embedding generation
4. Vector indexing in FAISS
5. Entity extraction and relationship creation
6. Graph storage in Neo4j

Duplicate document ingestion is prevented via document hashing.

---

## Querying the System

### Endpoint

```
POST /ask
```

### Example Request

```bash
curl -X POST "http://localhost:8000/ask?q=What policies apply to Entity X?"
```

### Example Response

```json
{
  "answer": "Policy ABC applies to Entity X under condition Y.",
  "sources": [
    {
      "document_id": "DOC_123",
      "page_number": 4,
      "chunk_id": "DOC_123_p4_c1"
    }
  ],
  "knowledge": "internal"
}
```

---

## Provenance and Hallucination Guardrails

* Every answer includes explicit citations
* Answers clearly state whether they used:

  * Internal knowledge only
  * Online sources only
  * Both
* If the answer is not found internally, the system states this explicitly rather than hallucinating

---

## Observability and Reliability

The system includes:

* Structured logging for OCR, retrieval, and tool calls
* Explicit error handling for:

  * OCR failures
  * Empty retrieval results
  * External tool failures

---

## Constraints and Notes

* Azure Document Intelligence inline OCR limit:

  * Maximum PDF size: **5 MB**
  * Maximum pages: **300**
* Designed as a **weekend take-home prototype**, but with production-oriented architecture
* For large-scale ingestion, async Textract with S3 would be recommended

---

## Project Structure

```
hybrid-llm-agent/
├── app/                # FastAPI app and agent logic
├── ingestion/          # OCR and ingestion pipeline
├── graph/              # Neo4j graph logic
├── vectorstore/        # FAISS vector index
├── observability/      # Logging utilities
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## Future Improvements

* Layout-aware chunking (tables, headings)
* OCR confidence scoring
* Hybrid ranking strategies (graph + vector)
* Evaluation harness (precision@k, citation accuracy)
* Authentication and multi-user support

---

## Design Rationale

This system demonstrates:

* True hybrid retrieval (semantic + symbolic)
* Robust ingestion of scanned documents
* Tool-based LLM reasoning
* Enterprise-grade traceability and observability