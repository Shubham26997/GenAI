import os
import uuid
import aiofiles
from typing import Optional
from fastapi import APIRouter, HTTPException, UploadFile
from pydantic import BaseModel
from lang_chain.document_loader import upload_document, SUPPORTED_EXTENSIONS
from lang_chain.query_pdf import chat_with_file

router = APIRouter()

# In-memory session store: session_id -> { filename, history }
# Each session is tied to one uploaded file and holds its full conversation history.
_sessions: dict[str, dict] = {}


# ---------- Response Models ----------

class StartChatResponse(BaseModel):
    session_id: str
    filename: str
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
    Upload a PDF and start a new chat session.
    Returns a session_id — use it in all subsequent /chat/{session_id}/message calls.
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

        filename = upload_document(file_path)

        session_id = str(uuid.uuid4())
        _sessions[session_id] = {"filename": filename, "history": []}

        return StartChatResponse(
            session_id=session_id,
            filename=filename,
            message=f"'{filename}' uploaded successfully. Start chatting using session_id."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


@router.post("/{session_id}/message", response_model=ChatResponse)
async def send_message(session_id: str, body: ChatRequest):
    """
    Send a message in an existing chat session.
    The LLM answers based on the uploaded file and remembers the full conversation history.
    """
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found. Upload a file at /chat/start first.")

    try:
        reply, updated_history = chat_with_file(
            user_input=body.message,
            filename=session["filename"],
            history=session["history"]
        )
        _sessions[session_id]["history"] = updated_history

        return ChatResponse(
            session_id=session_id,
            filename=session["filename"],
            reply=reply,
            history=updated_history
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
        history=session["history"]
    )


@router.delete("/{session_id}")
async def delete_session(session_id: str):
    """Clear a chat session and its history."""
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    del _sessions[session_id]
    return {"status": "ok", "message": f"Session '{session_id}' deleted"}
