# Module 3 — Zepto Support Assistant

## Architecture

```text
8 policy TXT files
      │
      ▼
  ingestion/chunking
      │
      ▼
all-MiniLM-L6-v2 embeddings
      │
      ▼
ChromaDB collection: zepto_policy
      │
      │ query embedding + top-3 cosine retrieval
      ▼
LangGraph intent router
   ┌── policy_question ──► retrieve_and_answer ──► grounded answer
   │
query
   │
   └── general_question ─► direct_answer ───────► fixed mock answer
```

### Stage-by-stage flow

1. **Ingestion:** `rag.py` reads every `.txt` file from `docs/` and creates one chunk per document. Each chunk keeps its document/chunk ID in ChromaDB metadata.
2. **Embedding:** `SentenceTransformer("all-MiniLM-L6-v2")` creates local vectors. No embedding API key is required.
3. **Retrieval:** `retrieve_and_answer` embeds the incoming query and asks ChromaDB for the top 3 nearest chunks using cosine distance.
4. **Generation:** In the graded default (`MOCK_LLM` unset or `1`), `retrieve_and_answer` returns a deterministic `Based on the retrieved context: ...` answer and `direct_answer` returns a fixed policy-only message. With `MOCK_LLM=0`, those generation branches can call Groq through the structured prompt.
5. **Validation:** the final response is validated by `SupportResponse`, containing `answer`, `sources`, and `confidence`.

The `MOCK_LLM` toggle changes only generation/classification behavior. Retrieval and embeddings remain real in both modes.

## Structured prompt

The optional real-LLM path uses a role–context–task–format–length prompt:

- **Role:** You are a Zepto policy support assistant.
- **Context:** only the retrieved policy chunks supplied in the prompt.
- **Task:** answer the customer's question from those chunks.
- **Format:** return JSON with `answer`, `sources`, and `confidence`.
- **Length:** keep the answer concise.
- **Negative constraint:** do not answer using information not present in the provided context.
- **Few-shot example:** the prompt contains a policy question and a grounded JSON answer.

## Local run

```bash
set MOCK_LLM=1
python -m uvicorn main:app --host 0.0.0.0 --port 7860
```

Linux/macOS:

```bash
export MOCK_LLM=1
python -m uvicorn main:app --host 0.0.0.0 --port 7860
```

## Example calls

### Retrieval path

```bash
curl -X POST http://localhost:7860/ask -H "Content-Type: application/json" -d "{\"query\":\"What is the delivery policy?\"}"
```

Expected response shape:

```json
{
  "answer": "Based on the retrieved context: ...",
  "sources": ["doc_01_chunk_0", "..."],
  "confidence": 1.0
}
```

### Direct path

```bash
curl -X POST http://localhost:7860/ask -H "Content-Type: application/json" -d "{\"query\":\"What is the capital of France?\"}"
```

Expected response shape:

```json
{
  "answer": "I can only answer questions about Zepto policies right now.",
  "sources": [],
  "confidence": 1.0
}
```

## Docker

```bash
docker build -t zepto-support-assistant .
docker run --rm -p 7860:7860 -e MOCK_LLM=1 zepto-support-assistant
```

The Dockerfile starts Uvicorn on port 7860 and does not require a paid service.

## Optional real LLM

Set `MOCK_LLM=0` and provide the required Groq credentials in the runtime environment. Never hardcode API keys or commit them. The code retries invalid structured output up to two additional times before returning a marked error response.
