import os
import aiofiles
from fastapi import APIRouter, UploadFile, HTTPException
from lang_chain.document_loader import upload_document, SUPPORTED_EXTENSIONS

router = APIRouter()

@router.post("/add_file/")
async def add_db_file(file: UploadFile):
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
        async with aiofiles.open(file_path, mode='wb') as f:
            while chunks := await file.read(1024 * 1024):
                await f.write(chunks)
        print("File saved locally, uploading to vector DB...")
        filename = upload_document(file_path)
        return {"status": "ok", "filename": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)