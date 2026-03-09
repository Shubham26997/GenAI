# import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore

# file_path = os.path.join(os.getcwd(), "Shubham Resume.pdf")
# print(file_path)
def upload_pdf(file_path):
    print("Loading PDF file...")
    pdf_file = PyPDFLoader(file_path)
    docs = pdf_file.load()
    print(f"Loaded {len(docs)} documents from the PDF.")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    split_text_chunks = text_splitter.split_documents(documents=docs)
    print(f"Split into {len(split_text_chunks)} text chunks.")

    emedding = OpenAIEmbeddings(
        model="text-embedding-ada-002",
    )

    try:
        vector_db_loading = QdrantVectorStore.from_documents(
            documents=split_text_chunks,
            embedding=emedding,
            collection_name="my_resume",
            url="http://vector_db:6333"
        )
        print("Successfully uploaded embeddings to Qdrant.")
    except Exception as e:
        print(f"Error during upload to Qdrant: {e}")
    return True