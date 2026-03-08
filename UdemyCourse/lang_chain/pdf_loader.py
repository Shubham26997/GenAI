import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore

file_path = os.path.join(os.getcwd(), "Shubham Resume.pdf")
# print(file_path)
pdf_file = PyPDFLoader(file_path)
docs = pdf_file.load()
# print(docs[0])

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size = 1000,
    chunk_overlap = 200
)
split_text_chunks = text_splitter.split_documents(documents = docs)

emedding = OpenAIEmbeddings(
    model = "text-embedding-ada-002",
)

vector_db_loading = QdrantVectorStore.from_documents(
    documents = split_text_chunks,
    embedding=emedding,
    collection_name="my_resume",
    url = "http://vector_db:6333"
)