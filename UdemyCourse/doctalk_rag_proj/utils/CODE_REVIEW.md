# Code Review: UdemyCourse

## Project Overview

A FastAPI-based AI application with RAG (Retrieval-Augmented Generation) capabilities using LangChain, OpenAI, and Qdrant vector database. Supports PDF ingestion, semantic querying, and an agentic workflow with tool use.

---

## Issues Found

### Critical (Security)

| # | File | Issue |
|---|------|-------|
| 1 | `.env` | Real OpenAI API key committed — rotate immediately and ensure `.gitignore` excludes `.env` |
| 2 | `my_agents/weather.py` | `run_cmd(cmd)` executes arbitrary OS commands via `os.system(cmd)` — remote code execution risk if ever exposed via API |
| 3 | `lang_chain/query_pdf.py` | Raw vector DB retrieved content injected directly into system prompt via f-string — malicious PDF content can manipulate LLM behavior |

---

### Major Issues

| # | File | Issue |
|---|------|-------|
| 4 | `router/file_upload.py`, `router/get_file.py` | Zero error handling — any failure (bad PDF, Qdrant down) returns unhandled 500 |
| 5 | `router/file_upload.py` | No file type validation — any file type can be uploaded, not just PDFs |
| 6 | `lang_chain/query_pdf.py` | `QdrantVectorStore.from_existing_collection()` called on every request — should be a module-level singleton |
| 7 | `lang_chain/query_pdf.py` | `sys.path.append(os.getcwd())` used for imports — fragile and bad practice |
| 8 | `router/file_upload.py`, `router/get_file.py` | No Pydantic `response_model` defined on endpoints — no type safety, validation, or auto-docs |
| 9 | `router/file_upload.py` | Uploaded files in `temp/` never cleaned up after embedding — accumulates indefinitely |
| 10 | `lang_chain/pdf_loader.py` | `upload_pdf()` always returns `True` even when Qdrant upload fails — exception is silently swallowed |

---

### Moderate Issues

| # | File | Issue |
|---|------|-------|
| 11 | `lang_chain/pdf_loader.py`, `lang_chain/query_pdf.py` | Typo: `emedding` should be `embedding` |
| 12 | `lang_chain/query_pdf.py` | Typos in system prompt: `relvent` → `relevant`, `Assitant` → `Assistant` |
| 13 | `my_agents/system_prompt.py` | Typo: `Availabe` → `Available` |
| 14 | `lang_chain/pdf_loader.py`, `lang_chain/query_pdf.py` | Collection name `"my_resume"` hardcoded — should be a parameter or config constant |
| 15 | All files | `print()` used everywhere — no log levels, no timestamps, not suitable for production |
| 16 | `lang_chain/chatbot.py` | Unused dead code — defines its own `FastAPI` app never imported by `api.py`, uses deprecated LangChain APIs |
| 17 | `Dockerfile` | Default `CMD` runs `my_agents/main.py` (interactive CLI), not the API server |
| 18 | `rag/main.py` | Empty placeholder — just `print("Hellow World!!")` |
| 19 | `api.py` | No CORS middleware — will block browser-based frontends |

---

### Minor / Polish

| # | File | Issue |
|---|------|-------|
| 20 | `router/get_file.py` | No health check endpoint — useful for Docker/load balancer readiness |
| 21 | `lang_chain/query_pdf.py` | `if user_input in ["exit", "exit()"]` is CLI logic leaking into an API function |
| 22 | `router/get_file.py` | `query_file()` is synchronous but called from `async` FastAPI route without `run_in_executor` — blocks the event loop |
| 23 | `lang_chain/pdf_loader.py`, `lang_chain/query_pdf.py` | Embedding model `text-embedding-ada-002` is outdated — `text-embedding-3-small` is cheaper and more accurate |
| 24 | `Dockerfile` | Missing `EXPOSE 8000` declaration |
| 25 | Root, `temp/` | Binary PDF files (`B2B_Invoices.pdf`, `Shubham Resume.pdf`) committed to git — should be gitignored |

---

## Improvements To Make

### 1. Security Hardening

- **Rotate the exposed OpenAI API key** immediately via the OpenAI dashboard.
- **Remove `run_cmd()`** from `my_agents/weather.py` and `my_agents/system_prompt.py`. If OS command execution is genuinely needed, it must be sandboxed (e.g., Docker-in-Docker, restricted subprocess with allowlist).
- **Sanitize RAG context before injecting into prompts** — wrap retrieved docs in clear delimiters and strip or escape user-controllable content:
  ```python
  system_prompt = f"""
  <context>
  {retrieved_docs}
  </context>
  Answer only based on the above context.
  """
  ```
- **Add `.env` to `.gitignore`** and use a `.env.example` file with placeholder values for onboarding.

---

### 2. API Robustness

- **Add file type validation** in the upload endpoint:
  ```python
  if not file.filename.endswith(".pdf") or file.content_type != "application/pdf":
      raise HTTPException(status_code=400, detail="Only PDF files are accepted")
  ```
- **Wrap all routes in try/except** and return structured error responses:
  ```python
  try:
      upload_pdf(file_path)
  except Exception as e:
      raise HTTPException(status_code=500, detail=str(e))
  ```
- **Define Pydantic response models** for every endpoint:
  ```python
  class UploadResponse(BaseModel):
      status: str
      filename: str

  @router.post("/add_pdf_file/", response_model=UploadResponse)
  ```
- **Add a health check endpoint** in `api.py`:
  ```python
  @app.get("/health")
  def health():
      return {"status": "ok"}
  ```
- **Add CORS middleware** if a frontend will ever consume this API:
  ```python
  from fastapi.middleware.cors import CORSMiddleware
  app.add_middleware(CORSMiddleware, allow_origins=["*"], ...)
  ```

---

### 3. Performance

- **Cache the Qdrant vector store** at module level instead of reinitializing on every request:
  ```python
  # module level
  _vector_db = None

  def get_vector_db():
      global _vector_db
      if _vector_db is None:
          _vector_db = QdrantVectorStore.from_existing_collection(...)
      return _vector_db
  ```
- **Run blocking I/O in a thread pool** to avoid blocking FastAPI's async event loop:
  ```python
  import asyncio
  result = await asyncio.get_event_loop().run_in_executor(None, query_file, query)
  ```
- **Clean up uploaded files** after processing:
  ```python
  finally:
      if os.path.exists(file_path):
          os.remove(file_path)
  ```

---

### 4. Code Quality

- **Replace `print()` with Python's `logging` module** throughout:
  ```python
  import logging
  logger = logging.getLogger(__name__)
  logger.info("Loaded %d documents from PDF", len(docs))
  ```
- **Fix all typos**: `emedding` → `embedding`, `relvent` → `relevant`, `Assitant` → `Assistant`, `Availabe` → `Available`
- **Parameterize the collection name** instead of hardcoding `"my_resume"`:
  ```python
  COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "documents")
  ```
- **Remove CLI-specific logic from API functions** (`query_file` exit check).
- **Delete dead code**: `lang_chain/chatbot.py`, `rag/main.py`.
- **Fix Dockerfile CMD** to point to the API server:
  ```dockerfile
  EXPOSE 8000
  CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
  ```

---

### 5. Upgrade Dependencies

| Current | Recommended | Reason |
|---------|-------------|--------|
| `text-embedding-ada-002` | `text-embedding-3-small` | 5x cheaper, higher accuracy |
| `gpt-4o` (hardcoded) | Config via env var `OPENAI_MODEL` | Easier model switching |
| Deprecated LangChain APIs in `chatbot.py` | Remove file or rewrite with current API | Avoid future breakage |

---

### 6. Project Structure (Longer Term)

```
UdemyCourse/
├── app/
│   ├── api.py               # FastAPI entry point
│   ├── config.py            # All env vars and constants in one place
│   ├── router/
│   ├── services/            # Business logic (pdf_loader, query, embeddings)
│   └── agents/
├── tests/                   # Unit + integration tests
├── .env.example             # Template with placeholder values
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

- Extract all configuration (URLs, model names, collection names) into a single `config.py` using `pydantic-settings`.
- Add a `tests/` directory with at least basic endpoint smoke tests using `pytest` + `httpx`.

---

## What's Done Well

- Pydantic `PromptOutput` model for structured LLM output is clean and reusable.
- `VECTOR_DB_URL` uses an env var with a sensible fallback.
- Docker Compose uses an external network — good for multi-service infra separation.
- `get_weather()` is well-implemented: free API, proper error handling, country code resolution, no API key needed.
- Async file chunked upload using `aiofiles` is the right pattern.
