import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore

VECTOR_DB_URL = os.getenv("VECTOR_DB_URL", "http://localhost:6333")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "pdf_documents")

def upload_pdf(file_path):
    print("Loading PDF file...")
    pdf_file = PyPDFLoader(file_path)
    docs = pdf_file.load()
    print(f"Loaded {len(docs)} documents from the PDF.")

    # Tag every chunk with the original filename so we can filter by it at query time
    filename = os.path.basename(file_path)
    for doc in docs:
        doc.metadata["filename"] = filename

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    split_text_chunks = text_splitter.split_documents(documents=docs)
    print(f"Split into {len(split_text_chunks)} text chunks.")

    embedding = OpenAIEmbeddings(
        model="text-embedding-ada-002",
    )

    try:
        QdrantVectorStore.from_documents(
            documents=split_text_chunks,
            embedding=embedding,
            collection_name=COLLECTION_NAME,
            url=VECTOR_DB_URL
        )
        print(f"Successfully uploaded embeddings for '{filename}' to Qdrant.")
    except Exception as e:
        print(f"Error during upload to Qdrant: {e}")
        raise
    return filename
