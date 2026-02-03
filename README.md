# Hybrid LLM Knowledge Agent

## Overview

This repository contains a **production‑oriented hybrid LLM knowledge agent** designed to ingest **scanned (image‑based) PDFs**, extract structured and unstructured knowledge, and answer user questions with **strong provenance guarantees**.

The system combines:

* **Neural retrieval** (vector embeddings)
* **Symbolic reasoning** (knowledge graph)
* **Tool‑orchestrated LLM agents**

Internal document knowledge is always prioritized. **External web search is used only as an explicit fallback**, never silently.

---

## Repository Structure (Complete)

```text
hybrid-llm-agent/
├── app/                    # FastAPI application layer
│   ├── main.py # FastAPI entrypoint: /ask and /ingest/pdf APIs
│   ├── agent.py # Core decision engine (graph-first / vector-first logic)
│   ├── tools.py # Retrieval tools: vector, graph, and online search
│   ├── language.py # Language detection (langdetect wrapper)
│   └── config.py # Environment configuration (SERPAPI keys, etc.)
│
├── ingestion/              # PDF ingestion & processing pipeline
│   ├── ingest.py # End-to-end ingestion pipeline coordinator
│   ├── dedup.py # Document hashing & deduplication
│   ├── ocr.py # Azure Document Intelligence OCR
│   ├── chunking.py # Page-aware chunking logic
│   └── embeddings.py # Embedding generation
│
├── vectorstore/             # Vector retrieval layer
│   ├── faiss_store.py       # FAISS index management
│   └── retriever.py         # Similarity search abstraction
│
├── graph/                   # Knowledge graph layer (Neo4j)
│   ├── neo4j_client.py      # Neo4j connection & session handling
│   └── graph_builder.py     # Graph construction from extracted entities
│
├── observability/           # Logging
│   ├── logging.py           # Structured logging setup
│
├── ui/                      # Chat / UI integration
│   └── chainlit_app.py      # Chainlit‑based conversational UI
│
├── data/                    # Local persistence
│
├── Dockerfile               # API container definition
├── docker-compose.yml       # API + Neo4j orchestration
├── requirements.txt         # Runtime Python dependencies
├── chainlit.md              # Chainlit UI documentation
├── Neo4j-*.txt              # Sample Neo4j export / debug dump
└── README.md                # Project documentation
```

---

## High‑Level Architecture

```text
User
 ↓
API / Chat Interface (FastAPI / Chainlit)
 ↓
LLM Agent (Tool‑Orchestrated)
 ├── Vector Search (FAISS)
 ├── Graph Reasoning (Neo4j)
 └── Online Search (SerpAPI – fallback only)
 ↓
Answer + Citations + Knowledge Source
```

---

## Core Design Principles

1. **Hybrid Retrieval** – Neural similarity + symbolic graph traversal
2. **Traceability First** – Every answer is cited
3. **No Silent Hallucination** – Missing knowledge is stated explicitly
4. **Tool Isolation** – Each capability is a separate, testable tool
5. **Production‑Ready Skeleton** – Clear separation of concerns

---

## PDF Ingestion Pipeline (Detailed)

1. **Upload** via `/ingest/pdf`
2. **Document Hashing** – Prevents duplicate ingestion
3. **OCR Extraction** – Azure Document Intelligence
4. **Text Normalization** – Cleanup & segmentation
5. **Chunking** – Page‑aware, citation‑ready chunks
6. **Embedding Generation** – Stored with metadata
7. **Vector Indexing** – FAISS similarity search
8. **Entity Extraction** – Concepts, entities, relations
9. **Graph Construction** – Nodes + relationships in Neo4j

All stages are logged and failure‑aware.

---

## Query Flow (Detailed)

1. User submits question via `/ask`
2. LLM agent determines retrieval strategy
3. **Vector search** for semantic grounding
4. **Graph queries** for relationships & constraints
5. **Answer synthesis** with citations
6. **Fallback to online search** only if internal knowledge is insufficient

The response explicitly declares the **knowledge source** used:

* `internal`
* `online`
* `hybrid`

---

## API Endpoints

### `POST /ingest/pdf`

**Purpose:** Ingest scanned PDFs

**Request:**

* `multipart/form-data`
* Field: `file` (PDF only)

**Response:**

```json
{
  "status": "success",
  "document_id": "<hash>",
  "pages_ingested": 12,
  "chunks_created": 58,
  "entities_created": 2468
}
```

---

### `POST /ask`

**Purpose:** Ask questions against the knowledge base

**Example:**

```bash
curl -X POST "http://localhost:8000/ask?q=What does section 4 say?"
```

**Response:**

```json
{
  "answer": "...",
  "sources": [
    {"document_id": "DOC1", "page_number": 3, "chunk_id": "c2", "text": "xxxx"}
  ],
  "knowledge": "internal"
}
```

---

## Observability

* Structured logs for every ingestion & query step
* Explicit tool‑level tracing
* Clear error messages for:

  * OCR failures
  * Empty retrieval
  * External API issues

---

## Installation & Setup

### 1. Create virtual environment (recommended)

```bash
python -m venv .venv
source .venv/bin/activate  # Linux / Mac
# .venv\Scripts\activate  # Windows
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Download spaCy language model

This project relies on **spaCy** for entity extraction during ingestion.

```bash
python -m spacy download en_core_web_sm
```

---

## Running the System

### Option 1: Run API locally (development)

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

* API available at: [http://localhost:8000](http://localhost:8000)

---

### Option 2: Run Chat UI (Chainlit)

```bash
chainlit run ui/chainlit_app.py
```

* Chat UI available at: [http://localhost:8000](http://localhost:8000)

---

### Option 3: Run full stack with Docker

```bash
docker compose up --build
```

Services:

* API: [http://localhost:8000](http://localhost:8000)
* Neo4j: [http://localhost:7474](http://localhost:7474)

  * user: `neo4j`
  * password: `password`

---

## Environment Variables

```env
OPENAI_API_KEY=sk-xxxx
SERPAPI_KEY=xxxx
AZURE_DOCUMENT_INTELLIGENCE_KEY=xxxx
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=xxxx
```

---

## Constraints & Notes

* Azure inline OCR limit: **20 MB / 300 pages**
* Designed as a **take‑home / prototype system** with real production patterns
* Easily extensible to async OCR, S3, or alternative vector DBs

---

## Summary

This project demonstrates a **fully traceable hybrid RAG system** that cleanly separates concerns, avoids hallucination, and provides a strong foundation for enterprise‑grade document intelligence systems.
