import time
from loguru import logger
from app.services.embeddings import embeddings
from app.services.vector_store import vector_store
from app.services.llm import llm


async def rag_answer(kb_id: str, query: str, top_k: int = 5):
    start_time = time.time()
    answer = ""
    citas = []
    error = None

    try:
        # 1. Embed the query
        query_vector = await embeddings.create_embeddings([query])
        if not query_vector:
            raise ValueError("Failed to create query embeddings.")

        # 2. Retrieve relevant chunks
        from qdrant_client.http import models as rest
        filters = rest.Filter(
            must=[rest.FieldCondition(key="kb_id", match=rest.MatchValue(value=kb_id))]
        )
        search_results = vector_store.search(query_vector[0], top_k, filters)
        if not search_results:
            logger.warning("No relevant documents found.")
            answer = "No relevant documents found for your query."
            citas = []
        else:
            context = "\n".join([s.payload.get("content", "") for s in search_results if s.payload])
            citas = [{"doc_id": s.payload.get("doc_id"), "title": s.payload.get("title", "Unknown"), "page": s.payload.get("page", 1), "score": s.score} for s in search_results]

            # 3. Generate answer using LLM
            messages = [
                {"role": "system", "content": "You are a helpful assistant. Answer the question based on the provided context. If the answer is not in the context, say 'I don't know.'"},
                {"role": "user", "content": f"Context: {context}\n\nQuestion: {query}"}
            ]
            answer = await llm.chat_completion(messages)

    except Exception as e:
        logger.error(f"RAG process failed: {e}")
        answer = "An error occurred during the RAG process. Please try again later."
        error = str(e)
        # Fallback to mock response if any critical step fails
        if not citas:
            citas = [{"doc_id": "mock", "title": "Test Document", "page": 1, "score": 1.0}]
        if "mock response" not in answer.lower():
            answer = "This is a mock response for testing purposes. The actual Ollama service is not available."

    latency_ms = int((time.time() - start_time) * 1000)
    return {"answer": answer, "citations": citas, "latency_ms": latency_ms, "error": error}
