from typing import Optional
from fastapi import APIRouter, HTTPException
from lang_chain.query_pdf import query_file

router = APIRouter()

@router.post("/query_file/")
async def query_pdf_file(query: str, filename: Optional[str] = None):
    """
    Query the vector DB.
    - Pass `filename` (e.g. `resume.pdf`) to search only within that document.
    - Omit `filename` to search across all uploaded documents.
    """
    try:
        return query_file(query, filename=filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))