import os
import uuid
import asyncio
import aiofiles
from fastapi import APIRouter, HTTPException, UploadFile
from pydantic import BaseModel
from lang_chain.pageindex_indexer import build_index
from lang_chain.pageindex_querier import chat_with_pageindex
from lang_chain.document_loader import SUPPORTED_EXTENSIONS

router = APIRouter()

# In-memory session store: session_id -> { filename, history }
_sessions: dict[str, dict] = {}


# ---------- Response Models ----------

class StartChatResponse(BaseModel):
    session_id: str
    filename: str
    doc_name: str
    message: str

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    session_id: str
    filename: str
    reply: str
    history: list[dict]

class SessionInfoResponse(BaseModel):
    session_id: str
    filename: str
    turn_count: int
    history: list[dict]


# ---------- Endpoints ----------

@router.post("/start", response_model=StartChatResponse)
async def start_chat(file: UploadFile):
    """
    Upload a PDF and build its PageIndex tree locally (self-hosted, no cloud key).
    Returns a session_id for all subsequent /chat/{session_id}/message calls.
    """
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    upload_dir = "temp"
    file_path = os.path.join(upload_dir, file.filename)
    os.makedirs(upload_dir, exist_ok=True)

    try:
        async with aiofiles.open(file_path, mode="wb") as f:
            while chunks := await file.read(1024 * 1024):
                await f.write(chunks)

        # page_index_main() internally calls asyncio.run(), which cannot be
        # nested inside FastAPI's running event loop. Run it in a thread so
        # it gets its own clean event loop.
        tree = await asyncio.to_thread(build_index, file_path, file.filename)

        session_id = str(uuid.uuid4())
        _sessions[session_id] = {
            "filename": file.filename,
            "history": [],
        }

        return StartChatResponse(
            session_id=session_id,
            filename=file.filename,
            doc_name=tree.get("doc_name", file.filename),
            message=f"PageIndex tree built for '{file.filename}'. Start chatting!",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


@router.post("/{session_id}/message", response_model=ChatResponse)
async def send_message(session_id: str, body: ChatRequest):
    """
    Chat with the document using PageIndex tree navigation.
    Step 1: LLM selects relevant sections from the tree.
    Step 2: Raw page text is extracted and passed to the LLM to answer.
    """
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found. Upload a file at /chat/start first.",
        )

    try:
        reply, updated_history = await asyncio.to_thread(
            chat_with_pageindex,
            body.message,
            session["filename"],
            session["history"],
        )
        _sessions[session_id]["history"] = updated_history

        return ChatResponse(
            session_id=session_id,
            filename=session["filename"],
            reply=reply,
            history=updated_history,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}", response_model=SessionInfoResponse)
async def get_session(session_id: str):
    """Get session details and full conversation history."""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionInfoResponse(
        session_id=session_id,
        filename=session["filename"],
        turn_count=len(session["history"]) // 2,
        history=session["history"],
    )


@router.delete("/{session_id}")
async def delete_session(session_id: str):
    """Clear a chat session and its history."""
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    del _sessions[session_id]
    return {"status": "ok", "message": f"Session '{session_id}' deleted"}
