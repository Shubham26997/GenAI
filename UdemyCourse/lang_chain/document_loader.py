import os
from langchain_community.document_loaders import (
    PyPDFLoader,
    CSVLoader,
    Docx2txtLoader,
    TextLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_core.documents import Document

VECTOR_DB_URL = os.getenv("VECTOR_DB_URL", "http://localhost:6333")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "pdf_documents")

SUPPORTED_EXTENSIONS = {".pdf", ".xlsx", ".xls", ".csv", ".docx", ".txt"}


def _load_file(file_path: str) -> list[Document]:
    """Load a file into LangChain Documents based on its extension."""
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        return PyPDFLoader(file_path).load()

    if ext in (".xlsx", ".xls"):
        try:
            import pandas as pd
        except ImportError:
            raise RuntimeError("pandas and openpyxl are required for Excel files. Add them to requirements.txt.")
        xl = pd.ExcelFile(file_path)
        docs = []
        for sheet_name in xl.sheet_names:
            df = xl.parse(sheet_name).fillna("")
            text = df.to_string(index=False)
            docs.append(Document(
                page_content=text,
                metadata={"source": file_path, "sheet": sheet_name},
            ))
        return docs

    if ext == ".csv":
        return CSVLoader(file_path).load()

    if ext == ".docx":
        return Docx2txtLoader(file_path).load()

    if ext == ".txt":
        return TextLoader(file_path, encoding="utf-8").load()

    raise ValueError(f"Unsupported file type: '{ext}'. Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}")


def upload_document(file_path: str) -> str:
    """
    Load any supported file, chunk it, embed it, and store in Qdrant.
    Returns the original filename.
    """
    filename = os.path.basename(file_path)
    print(f"Loading file: {filename}")

    docs = _load_file(file_path)
    print(f"Loaded {len(docs)} document(s).")

    for doc in docs:
        doc.metadata["filename"] = filename

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )
    chunks = text_splitter.split_documents(docs)
    print(f"Split into {len(chunks)} chunks.")

    embedding = OpenAIEmbeddings(model="text-embedding-ada-002")

    try:
        QdrantVectorStore.from_documents(
            documents=chunks,
            embedding=embedding,
            collection_name=COLLECTION_NAME,
            url=VECTOR_DB_URL,
        )
        print(f"Uploaded embeddings for '{filename}' to Qdrant.")
    except Exception as e:
        print(f"Error uploading to Qdrant: {e}")
        raise

    return filename
