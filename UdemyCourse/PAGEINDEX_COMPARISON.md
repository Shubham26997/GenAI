# PageIndex vs Vector RAG — Migration Analysis

Reference: https://github.com/VectifyAI/PageIndex?tab=readme-ov-file

---

## How Each Pipeline Works

**Current (Vector RAG)**
```
PDF → Chunk (1000 chars, 200 overlap) → Embed (OpenAI ada-002) → Store in Qdrant → Similarity Search → LLM
```

**PageIndex**
```
PDF → Build hierarchical tree index (Table of Contents style) → LLM reasons through tree → LLM
```

No vectors. No Qdrant. No chunking. The LLM navigates the document structure itself to find relevant sections.

Core insight from PageIndex: **similarity ≠ relevance** — vector similarity finds text that *looks alike*, not text that *answers the question*.

---

## Changes Required

### `requirements.txt`
```diff
- langchain-qdrant
- langchain-text-splitters
- langchain-openai          # used only for embeddings, not LLM calls
+ pageindex                 # install from VectifyAI/PageIndex repo
```
`langchain`, `openai`, `fastapi`, `aiofiles` all stay unchanged.

---

### `lang_chain/pdf_loader.py`
The entire chunk → embed → Qdrant store logic is replaced by building and saving a tree index.

```python
# Before
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
chunks = text_splitter.split_documents(docs)
QdrantVectorStore.from_documents(chunks, embedding=..., collection_name=...)

# After
from pageindex import PageIndex
index = PageIndex(pdf_path=file_path, api_key=os.getenv("OPENAI_API_KEY"))
index.build()
index.save(f"indexes/{filename}.json")  # tree index saved as a plain JSON file
```

---

### `lang_chain/query_pdf.py`
Similarity search replaced with LLM reasoning over the tree index.

```python
# Before
vector_db.similarity_search(user_input, filter=filter_by_filename)

# After
from pageindex import PageIndex
index = PageIndex.load(f"indexes/{filename}.json")
result = index.query(user_input)  # LLM traverses tree, returns relevant pages + reasoning
```

---

### `docker-compose.yml`
Qdrant service dependency removed entirely.

```diff
  services:
    application:
      ...
-     environment:
-       - VECTOR_DB_URL=http://qdrant_db:6333
```

The `infra_network` external dependency on Qdrant also goes away.

---

### `.env`
```diff
- VECTOR_DB_URL=http://qdrant_db:6333
- QDRANT_COLLECTION=pdf_documents
  OPENAI_API_KEY=...
```

---

### `router/chat.py`
No changes needed. Session management, file upload, and conversation history all stay the same. Only the internal `chat_with_file()` call is affected since it delegates to the updated query logic.

---

## Benefits

| Area | Current (Vector RAG) | PageIndex |
|------|----------------------|-----------|
| **Accuracy** | Depends on chunk quality and embedding similarity | LLM reasons about relevance directly |
| **Structured docs** | Chunks break tables, headers, numbered lists | Preserves natural document structure |
| **Invoice tables** | Table rows split across chunks → wrong totals | Full table read as one unit → accurate |
| **Infrastructure** | Qdrant running, external network, vector store management | Just a `.json` file per document |
| **Upload cost** | Embedding cost (API call) per chunk on every upload | No embedding cost — only LLM calls at query time |
| **Interpretability** | "top-k similar chunks" — opaque, no source reference | Returns page numbers + reasoning trace |
| **Duplicate uploads** | Same file re-uploaded silently adds duplicate vectors | Index is a file — trivial to check if it already exists |

---

## Drawbacks

| Drawback | Details |
|----------|---------|
| **Query latency** | Multiple LLM calls per query to traverse the tree — slower than a single vector lookup |
| **Cost per query** | More tokens consumed per query compared to one embedding search |
| **Unstructured docs** | Works best with well-structured PDFs. Plain unorganised text benefits less |
| **Cross-document search** | Vector RAG searches all docs in one shot. PageIndex queries one document tree at a time — `filename` becomes mandatory on every query |
| **Library maturity** | Newer project vs. the battle-tested LangChain + Qdrant stack |

---

## Verdict for This Project

The two main document types in this project:

**Resumes** — highly structured (sections, bullet points, dates, headings)
→ PageIndex gives noticeably more accurate answers since section boundaries are respected.

**B2B Invoices** — table-heavy with numeric data
→ PageIndex is significantly better here. Chunking routinely splits invoice rows mid-table, causing wrong totals or missing line items. PageIndex reads the full table as a unit.

The infrastructure simplification (no Qdrant, no embedding pipeline) is a meaningful win at this scale. The tradeoff is higher per-query latency and LLM token usage since each query now makes multiple reasoning calls instead of one vector lookup.

**Recommendation:** Switch to PageIndex if query accuracy on invoices and structured documents is the priority. Stick with the current Vector RAG stack if low query latency or cross-document search is more important.
