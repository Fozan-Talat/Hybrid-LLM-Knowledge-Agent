from openai import OpenAI
from app.language import detect_language
from app.tools import vector_search, graph_search, online_search
from graph.graph_builder import extract_entities_smart

client = OpenAI()

def dedupe_chunks(chunks: list[dict]) -> list[dict]:
    seen = set()
    unique = []

    for c in chunks:
        key = (c["document_id"], c["page_number"], c["chunk_id"])
        if key not in seen:
            seen.add(key)
            unique.append(c)

    return unique

def is_non_answer(text: str) -> bool:
    triggers = [
        "does not contain information",
        "cannot be found in the context",
        "not mentioned in the context",
        "no information provided",

        # Arabic
        # "لا تتضمن",
        # "غير مذكور",
        # "لا يرد",
        # "لا يحتوي السياق",
        # "غير متوفر في النص"
    ]
    text_lower = text.lower()
    return any(t in text_lower for t in triggers)

def is_graph_intent(question: str) -> bool:
    lang = detect_language(question)
    # q = question.lower()

    # graph_triggers = [
    #     "list all entities",
    #     "list entities",
    #     "which entities",
    #     "what entities",
    #     "components of",
    #     "parts of",
    #     "related to",
    #     "relationships",
    #     "connections between",
    #     "how is .* related to"
    # ]

    # return any(trigger in q for trigger in graph_triggers)
    ents = extract_entities_smart(question, lang)
    return len(ents) > 0


def graph_query_from_question(question: str):
    lang = detect_language(question)
    ents = extract_entities_smart(question, lang)
    return ents[0]["name"] if ents else None

def is_document_specific(question: str) -> bool:
    triggers = [
        "هذا التقرير",
        "هذه الوثيقة",
        "في هذا التقرير",
        "عنوان التقرير",
        "الفصل",
        "الملحق"
    ]
    return any(t in question for t in triggers)

def answer(question: str):
    query_lang = detect_language(question)
    # 0. Detect graph-native intent
    if query_lang == "ar":
        doc_specific = is_document_specific(question)
    graph_intent = is_graph_intent(question)

    # 1. GRAPH-FIRST for graph-native questions
    if graph_intent:
        entity = graph_query_from_question(question)
        graph_hits = graph_search(entity)

        if graph_hits:
            graph_answer = synthesize(question, graph_hits, query_lang)

            if not is_non_answer(graph_answer):
                return {
                    "answer": graph_answer,
                    "sources": graph_hits,
                    "knowledge": "internal (graph)"
                }

        # If graph failed, THEN try vector
        internal_hits = dedupe_chunks(vector_search(question, query_lang))

        if internal_hits:
            vector_answer = synthesize(question, internal_hits, query_lang)

            if not is_non_answer(vector_answer):
                return {
                    "answer": vector_answer,
                    "sources": internal_hits,
                    "knowledge": "internal (vector-fallback)"
                }

        # Final fallback
        if (query_lang == 'ar'):
            allow_web = not doc_specific
        else:
            allow_web = True

        if (allow_web and query_lang == 'ar') or query_lang == 'en':
            online = online_search(question)
            return {
                "answer": online["organic_results"][0]["snippet"],
                "sources": online["organic_results"][0]["link"],
                "knowledge": "online"
            }

    # 2. VECTOR-FIRST for non-graph questions
    internal_hits = dedupe_chunks(vector_search(question, query_lang))

    if internal_hits:
        internal_answer = synthesize(question, internal_hits, query_lang)

        if not is_non_answer(internal_answer):
            return {
                "answer": internal_answer,
                "sources": internal_hits,
                "knowledge": "internal (vector)"
            }

        print("VECTOR HITS:", len(internal_hits))
        print("VECTOR ANSWER:", internal_answer)

        # Try graph if vector insufficient
        graph_hits = graph_search(question)

        if graph_hits:
            graph_answer = synthesize(question, graph_hits, query_lang)

            if not is_non_answer(graph_answer):
                return {
                    "answer": graph_answer,
                    "sources": graph_hits,
                    "knowledge": "internal (graph)"
                }

    # 3. External fallback
    online = online_search(question)
    return {
        "answer": online["organic_results"][0]["snippet"],
        "sources": online["organic_results"][0]["link"],
        "knowledge": "online"
    }

def synthesize(question: str, chunks: list[dict], lang: str) -> str:
    """
    Use the LLM to synthesize an answer grounded in retrieved chunks.
    """

    context = "\n\n".join(
        f"[Doc {c['document_id']} | Page {c['page_number']} | Chunk {c['chunk_id']}]\n{c['text']}"
        for c in chunks
    )

    if lang == 'en':
        prompt = f"""
You are a knowledge assistant.
Answer the question strictly using the provided context.
If the answer cannot be found in the context, say so explicitly.

Context:
{context}

Question:
{question}

Answer:
"""
    else:
        prompt = f"""
أنت مساعد يعتمد فقط على النص المقدم أدناه.
أجب عن السؤال باستخدام نفس الألفاظ الواردة في النص.
إذا كان السؤال عن عنوان الوثيقة، فاذكر العنوان حرفياً كما ورد.

إذا لم تجد الإجابة في النص، قل بوضوح: "لا يرد العنوان في النص".

السياق:
{context}

السؤال:
{question}

الإجابة:
"""


    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    return response.choices[0].message.content.strip()
