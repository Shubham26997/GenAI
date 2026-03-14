from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from router import file_upload, get_file, chat, pageindex_chat

app = FastAPI(
    title="PDF Reader",
    description="PDF Q&A — Vector DB (Qdrant) and PageIndex (vectorless) engines"
)

origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://0.0.0.0:8002",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Vector DB (Qdrant) routes
app.include_router(file_upload.router, prefix="/file")
app.include_router(get_file.router, prefix="/query")
app.include_router(chat.router, prefix="/chat")

# PageIndex (vectorless) routes
app.include_router(pageindex_chat.router, prefix="/pageindex/chat")


@app.get("/health")
def health():
    return {"status": "ok"}
