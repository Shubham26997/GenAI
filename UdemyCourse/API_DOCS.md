# PDF Chatbot API Documentation

A FastAPI application that lets you upload PDF files and chat with them using RAG (Retrieval-Augmented Generation) backed by OpenAI and Qdrant vector database.

---

## Base URL

```
http://localhost:8002
```

---

## Architecture Overview

```
Client
  │
  ├── POST /chat/start          Upload PDF → get session_id
  │         │
  │         ▼
  │   [Save to temp/]
  │   [Chunk + Embed via OpenAI]
  │   [Store in Qdrant with filename tag]
  │   [Create session in memory]
  │
  └── POST /chat/{session_id}/message    Send message → get reply
            │
            ▼
      [Filter Qdrant by filename]
      [Similarity search on query]
      [Build prompt: system + history + user message]
      [OpenAI gpt-4o response]
      [Append turn to session history]
      [Return reply + updated history]
```

**Key concepts:**
- Each uploaded file gets a `session_id` — a unique identifier for that chat session
- The session stores the full conversation history in memory
- Every new message includes prior turns so the LLM has context of the conversation
- Qdrant filters by `filename` so queries only search the relevant document's chunks

---

## Endpoints

### Health Check

#### `GET /health`

Check if the server is running.

**Response**
```json
{ "status": "ok" }
```

---

### Chat (PDF Chatbot)

#### `POST /chat/start`

Upload a PDF file and start a new chat session. Returns a `session_id` used for all subsequent messages.

**Request**
```
Content-Type: multipart/form-data
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | File | Yes | PDF file to upload (`.pdf` only) |

**Response `200`**
```json
{
  "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "filename": "invoice.pdf",
  "message": "'invoice.pdf' uploaded successfully. Start chatting using session_id."
}
```

**Error Responses**

| Status | Reason |
|--------|--------|
| `400` | File is not a PDF |
| `500` | Failed to embed or store in Qdrant |

**Example — curl**
```bash
curl -X POST http://localhost:8002/chat/start \
  -F "file=@/path/to/invoice.pdf"
```

**Example — Python**
```python
import requests

with open("invoice.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8002/chat/start",
        files={"file": ("invoice.pdf", f, "application/pdf")}
    )

data = response.json()
session_id = data["session_id"]
print(session_id)
```

---

#### `POST /chat/{session_id}/message`

Send a message within an existing chat session. The LLM answers based on the uploaded file and remembers all prior conversation turns.

**Path Parameter**

| Parameter | Type | Description |
|-----------|------|-------------|
| `session_id` | string | Session ID returned from `/chat/start` |

**Request Body**
```json
{ "message": "What is the total invoice amount?" }
```

**Response `200`**
```json
{
  "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "filename": "invoice.pdf",
  "reply": "The total invoice amount across all entries is ₹4,23,500.",
  "history": [
    { "role": "user",      "content": "What is the total invoice amount?" },
    { "role": "assistant", "content": "The total invoice amount across all entries is ₹4,23,500." }
  ]
}
```

**Error Responses**

| Status | Reason |
|--------|--------|
| `404` | Session not found — upload a file first at `/chat/start` |
| `500` | LLM or vector DB error |

**Example — curl**
```bash
curl -X POST http://localhost:8002/chat/a1b2c3d4-.../message \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the total invoice amount?"}'
```

**Example — Python**
```python
import requests

session_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"

response = requests.post(
    f"http://localhost:8002/chat/{session_id}/message",
    json={"message": "What is the total invoice amount?"}
)
print(response.json()["reply"])
```

---

#### `GET /chat/{session_id}`

Retrieve session details and full conversation history.

**Path Parameter**

| Parameter | Type | Description |
|-----------|------|-------------|
| `session_id` | string | Session ID |

**Response `200`**
```json
{
  "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "filename": "invoice.pdf",
  "turn_count": 3,
  "history": [
    { "role": "user",      "content": "What is the total invoice amount?" },
    { "role": "assistant", "content": "The total invoice amount is ₹4,23,500." },
    { "role": "user",      "content": "Which vendor has the highest invoice?" },
    { "role": "assistant", "content": "Vendor XYZ has the highest invoice of ₹98,000." }
  ]
}
```

**Error Responses**

| Status | Reason |
|--------|--------|
| `404` | Session not found |

---

#### `DELETE /chat/{session_id}`

Delete a session and clear its conversation history from memory.

**Path Parameter**

| Parameter | Type | Description |
|-----------|------|-------------|
| `session_id` | string | Session ID to delete |

**Response `200`**
```json
{
  "status": "ok",
  "message": "Session 'a1b2c3d4-...' deleted"
}
```

**Error Responses**

| Status | Reason |
|--------|--------|
| `404` | Session not found |

---

### File Upload (standalone)

#### `POST /file/add_pdf_file/`

Upload a PDF and embed it into the vector DB without creating a chat session. Use this if you only want to store a document for later querying via `/query/query_file/`.

**Request**
```
Content-Type: multipart/form-data
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | File | Yes | PDF file to upload |

**Response `200`**
```json
{
  "status": "ok",
  "filename": "resume.pdf"
}
```

---

### Query (standalone)

#### `POST /query/query_file/`

Query the vector DB directly without a session or conversation history. Single-turn only.

**Query Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | The question to ask |
| `filename` | string | No | Restrict search to a specific file. Omit to search all documents. |

**Response `200`**
```json
{
  "step": "Analyse",
  "content": "The candidate has 3 years of experience in Python and FastAPI."
}
```

**Example — curl**
```bash
# Query a specific file
curl -X POST "http://localhost:8002/query/query_file/?query=years+of+experience&filename=resume.pdf"

# Query across all uploaded files
curl -X POST "http://localhost:8002/query/query_file/?query=total+amount"
```

---

## End-to-End Example

A complete chatbot session from upload to multi-turn conversation:

```python
import requests

BASE = "http://localhost:8002"

# 1. Upload PDF and start session
with open("B2B_Invoices.pdf", "rb") as f:
    res = requests.post(f"{BASE}/chat/start", files={"file": ("B2B_Invoices.pdf", f, "application/pdf")})

session_id = res.json()["session_id"]
print(f"Session started: {session_id}")

# 2. First message
res = requests.post(f"{BASE}/chat/{session_id}/message", json={"message": "Give me a summary of this document."})
print("Bot:", res.json()["reply"])

# 3. Follow-up — LLM remembers the previous turn
res = requests.post(f"{BASE}/chat/{session_id}/message", json={"message": "Which vendor appears most frequently?"})
print("Bot:", res.json()["reply"])

# 4. Another follow-up
res = requests.post(f"{BASE}/chat/{session_id}/message", json={"message": "What is the total amount for that vendor?"})
print("Bot:", res.json()["reply"])

# 5. Check history
res = requests.get(f"{BASE}/chat/{session_id}")
print(f"Total turns: {res.json()['turn_count']}")

# 6. Clean up
requests.delete(f"{BASE}/chat/{session_id}")
print("Session deleted")
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | — | Required. Your OpenAI API key |
| `VECTOR_DB_URL` | `http://localhost:6333` | Qdrant instance URL |
| `QDRANT_COLLECTION` | `pdf_documents` | Qdrant collection name |

---

## Interactive API Docs

FastAPI provides built-in interactive documentation once the server is running:

| UI | URL |
|----|-----|
| Swagger UI | `http://localhost:8002/docs` |
| ReDoc | `http://localhost:8002/redoc` |

---

## Known Limitations

- **Sessions are in-memory** — all sessions are lost on server restart. For persistence, replace `_sessions` dict with a Redis or database store.
- **No authentication** — any caller with the `session_id` can access a session.
- **Long conversations** — very long histories will eventually exceed the OpenAI token limit. Consider trimming history to the last N turns for production use.
- **Single file per session** — each session is locked to the file uploaded at `/chat/start`. To chat with a different file, start a new session.
