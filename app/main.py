from fastapi import FastAPI, Query, UploadFile, File, HTTPException
import tempfile
import os
import traceback

from app.agent import answer
from ingestion.ingest import ingest
from ingestion.dedup import document_hash

app = FastAPI(title="Hybrid LLM Knowledge Agent")

@app.post("/ask")
def ask(q: str):
    return answer(q)

@app.post("/ingest/pdf")
async def ingest_pdf(
    file: UploadFile = File(...),
    force: bool = Query(False, description="Force re-ingestion even if document already exists")
):
    # -------------------------
    # Validate file type
    # -------------------------
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported"
        )

    # -------------------------
    # Save to temp file
    # -------------------------
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            contents = await file.read()

            if len(contents) > 20 * 1024 * 1024:
                raise HTTPException(
                    status_code=400,
                    detail="PDF exceeds 20MB Azure Document Intelligence inline limit"
                )

            tmp.write(contents)
            tmp_path = tmp.name

        # -------------------------
        # Compute document ID
        # -------------------------
        doc_id = document_hash(tmp_path)

        # -------------------------
        # Run ingestion pipeline
        # -------------------------
        result = ingest(tmp_path, force=force)

        if result["status"] == "success":
            return {
                "status": "success",
                "document_id": doc_id,
                "pages_ingested": result["pages"],
                "chunks_created": result["chunks"],
                "entities_created": result["entities_created"]
            }
        else:
            return result

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ingestion failed: {str(e)}\n\n{''.join(traceback.format_tb(e.__traceback__))}"
        )

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
