import os
import aiofiles
from fastapi import APIRouter, UploadFile
from lang_chain.pdf_loader import upload_pdf
router = APIRouter()

@router.post("/add_pdf_file/")
async def add_db_pdf_file(file: UploadFile):
    upload_dir = "temp"
    file_path = os.path.join(upload_dir, file.filename)
    os.makedirs(upload_dir, exist_ok = True)
    async with aiofiles.open(file_path, mode='wb') as f:
        while chunks:=await file.read(1024 * 1024):
            await f.write(chunks)
    print("file loaded to local storage and now uploading to vector db...")
    upload_pdf(file_path)
    return {"status":"ok"}