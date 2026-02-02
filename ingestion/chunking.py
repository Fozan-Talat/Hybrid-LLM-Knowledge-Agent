from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100
)

def chunk_pages(doc_id: str, pages: list[dict]) -> list[dict]:
    chunks = []
    for page in pages:
        texts = splitter.split_text(page["text"])
        for idx, t in enumerate(texts):
            chunks.append({
                "document_id": doc_id,
                "page_number": page["page_number"],
                "chunk_id": f"{doc_id}_p{page['page_number']}_c{idx}",
                "text": t
            })
    return chunks
