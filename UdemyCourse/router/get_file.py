from fastapi import APIRouter
from lang_chain.query_pdf import query_file
router = APIRouter()

@router.post("/query_file/")
async def query_pdf_file(query: str):
    return query_file(query)