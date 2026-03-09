from fastapi import FastAPI
from router import file_upload, get_file
app = FastAPI(
    title="PDF Reader Vector DB",
    description="PDF Q&A"
)

app.include_router(file_upload.router, prefix="/file")
app.include_router(get_file.router, prefix='/query')