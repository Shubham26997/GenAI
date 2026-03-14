import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client.models import Filter, FieldCondition, MatchValue
from openai import OpenAI
from my_agents.model import PromptOutput

load_dotenv()

COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "pdf_documents")

embedding = OpenAIEmbeddings(
    model="text-embedding-ada-002",
)

client = OpenAI()

# Cached at module level — initialized once on first query
_vector_db = None

def get_vector_db():
    global _vector_db
    if _vector_db is None:
        _vector_db = QdrantVectorStore.from_existing_collection(
            embedding=embedding,
            collection_name=COLLECTION_NAME,
            url=os.getenv("VECTOR_DB_URL", "http://localhost:6333")
        )
    return _vector_db

def generate_sys_prompt(retrieved_docs):
    context = "\n\n".join(doc.page_content for doc in retrieved_docs)
    system_prompt = f"""
        You are an expert AI Assistant who helps users analyse PDF documents.
        Answer the user's query based only on the relevant context retrieved from the document below.

        <context>
        {context}
        </context>

        Provide your response in the required JSON format.
    """
    return system_prompt

def query_file(user_input, filename: str = None):
    vector_db = get_vector_db()

    # If a filename is provided, filter chunks to only that document
    search_filter = None
    if filename:
        search_filter = Filter(
            must=[FieldCondition(key="metadata.filename", match=MatchValue(value=filename))]
        )

    vector_docs_db = vector_db.similarity_search(user_input, filter=search_filter)
    print(f"Retrieved {len(vector_docs_db)} chunks" + (f" from '{filename}'" if filename else " across all documents"))

    message_chat = [
        {
            "role": "system",
            "content": generate_sys_prompt(vector_docs_db)
        },
        {
            "role": "user",
            "content": user_input
        }
    ]
    response = client.chat.completions.parse(
        model="gpt-4o",
        response_format=PromptOutput,
        messages=message_chat
    )
    msg_resp = response.choices[0].message.parsed
    return {
        "step": msg_resp.step,
        "content": msg_resp.content
    }


def chat_with_file(user_input: str, filename: str, history: list[dict]) -> tuple[str, list[dict]]:
    """
    Conversational query against a specific file.

    Args:
        user_input:  The user's latest message.
        filename:    The file to restrict the search to.
        history:     Prior turns as [{"role": "user"/"assistant", "content": "..."}]

    Returns:
        (assistant_reply, updated_history)
    """
    vector_db = get_vector_db()

    search_filter = Filter(
        must=[FieldCondition(key="metadata.filename", match=MatchValue(value=filename))]
    )
    retrieved_docs = vector_db.similarity_search(user_input, filter=search_filter)
    print(f"Retrieved {len(retrieved_docs)} chunks from '{filename}'")

    # Build message list: system prompt + full conversation history + latest user message
    messages = [{"role": "system", "content": generate_sys_prompt(retrieved_docs)}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_input})

    response = client.chat.completions.parse(
        model="gpt-4o",
        response_format=PromptOutput,
        messages=messages
    )
    msg_resp = response.choices[0].message.parsed
    reply = msg_resp.content or ""

    # Append this turn to history and return it
    updated_history = history + [
        {"role": "user", "content": user_input},
        {"role": "assistant", "content": reply}
    ]
    return reply, updated_history

if __name__ == "__main__":
    while True:
        user_input = input("📩: ")
        if user_input in ["exit", "exit()"]:
            print("Bye!!")
            break
        query_file(user_input)
