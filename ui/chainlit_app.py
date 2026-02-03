import chainlit as cl
import requests

BACKEND_URL = "http://localhost:8000"

@cl.on_chat_start
async def start():
    await cl.Message(
        content=(
            "🧠 **Hybrid Knowledge Agent**\n\n"
            "- Graph-first for entity & relationship questions\n"
            "- Vector search for semantic questions\n"
            "- Online fallback if internal knowledge fails\n\n"
            "Ask a question from the knowledge base."
        )
    ).send()


@cl.on_message
async def handle_message(message: cl.Message):
    question = message.content.strip()

    if not question:
        return

    thinking = cl.Message(content="🔍 Thinking...")
    await thinking.send()

    try:
        resp = requests.post(
            f"{BACKEND_URL}/ask",
            params={"q": question},
            timeout=60
        )
        resp.raise_for_status()
        data = resp.json()

    except Exception as e:
        await thinking.remove()
        await cl.Message(
            content=f"❌ Error contacting backend:\n\n`{str(e)}`"
        ).send()
        return

    await thinking.remove()

    answer = data.get("answer", "No answer returned.")
    knowledge = data.get("knowledge", "unknown")
    sources = data.get("sources", [])

    # --- Main answer ---
    await cl.Message(
        content=f"### ✅ Answer\n\n{answer}"
    ).send()

    # --- Knowledge source ---
    await cl.Message(
        content=f"**Knowledge source:** `{knowledge}`"
    ).send()

    # --- Citations (chunks) ---
    if isinstance(sources, list) and sources:
        citation_text = "### 📚 Sources\n"
        for c in sources:
            citation_text += (
                f"- **Doc:** `{c.get('document_id')}` | "
                f"Page {c.get('page_number')} | "
                f"Chunk `{c.get('chunk_id')}`\n"
            )

        await cl.Message(content=citation_text).send()