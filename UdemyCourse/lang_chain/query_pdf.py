import os
import sys
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from openai import OpenAI
sys.path.append(os.getcwd())
from my_agents.model import PromptOutput

load_dotenv()
emedding = OpenAIEmbeddings(
    model = "text-embedding-ada-002",
)

vector_db = QdrantVectorStore.from_existing_collection(
    embedding=emedding,
    collection_name="my_resume",
    url = "http://vector_db:6333"
)
client = OpenAI()

def generate_sys_prompt(emeddings_db):
    system_prompt = f"""
        You are expert AI Assitant who help user analyse the pdf stored under a vector db based on the relvent query the user send. Based on the user query you will receive the relvent information from the db inside {emeddings_db} and you will provide the required output in below json format.

        Output:
            - '/{{"step": "Analyse", "content": "your name is Shubham Goel"}}/'
    """
    return system_prompt

def query_file(user_input):
    # user_input = input("📩: ")
    # print("User input is:", user_input)
    if user_input in ["exit", "exit()"]:
        print("Bye!!")
        return
    vector_docs_db = vector_db.similarity_search(user_input)
    print("Retrieved documents:", vector_docs_db)
    print("System prompt:", generate_sys_prompt(vector_docs_db))
    message_chat = [
        {
            "role": "system",
            "content": generate_sys_prompt(vector_docs_db)
        },
        {
            "role":"user",
            "content": user_input
        }
    ]      
    response = client.chat.completions.parse(
        model = "gpt-4o",
        response_format = PromptOutput,
        messages=message_chat
    )
        # print(response.choices[0].message.content)
        # msg_resp = json.loads(response.choices[0].message.content)
        # print(type(msg_resp))
    msg_resp = response.choices[0].message.parsed
    print("LLM response:", response)
    # print(msg_resp.content)
    return {
        "step": msg_resp.step,
        "content": msg_resp.content
    }

if __name__ == "__main__":
    while True:
        user_input = input("📩: ")
        # print("User input is:", user_input)
        query_file(user_input)
        if user_input in ["exit", "exit()"]:
            # print("Bye!!")
            break
