from app.config import AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT, AZURE_DOCUMENT_INTELLIGENCE_KEY
import os
from collections import defaultdict

from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential

azure_client = DocumentAnalysisClient(endpoint=AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT, credential=AzureKeyCredential(AZURE_DOCUMENT_INTELLIGENCE_KEY))

def ocr_pdf_with_azure(pdf_path: str) -> list[dict]:
    """
    OCR a scanned PDF using Azure Document Intelligence.
    Returns page-level text suitable for chunking & citation.
    """

    with open(pdf_path, "rb") as f:
        poller = azure_client.begin_analyze_document(
            model_id="prebuilt-read",
            document=f
        )

    result = poller.result()

    pages = defaultdict(list)

    for page in result.pages:
        page_number = page.page_number
        for line in page.lines:
            pages[page_number].append(line.content)

    return [
        {
            "page_number": page,
            "text": "\n".join(lines).strip()
        }
        for page, lines in sorted(pages.items())
    ]