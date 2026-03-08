import os
import sys
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from openai import OpenAI

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from my_agents.model import PromptOutput

load_dotenv()
SYSTEM_PROMPT = """
    You are expert AI Assitant who help user analyse the pdf stored under a vector db based on the relvent query the user send. Based on the user query you will receive the relvent information from the db and you will provide the required output in below json format.

    Your output information should be exactly limited to the content of pdf file not anything else is accepted.

    Output:
        - {"step": "Analyse", "content": "your name is Shubham Goel"}
"""
emedding = OpenAIEmbeddings(
    model = "text-embedding-ada-002",
)

vector_db = QdrantVectorStore.from_existing_collection(
    embedding=emedding,
    collection_name="my_resume",
    url = "http://vector_db:6333"
)
client = OpenAI()
while True:
    user_input = input("📩: ")
    # print("User input is:", user_input)
    if user_input in ["exit", "exit()"]:
        print("Bye!!")
        break
    message_chat = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },
        {
            "role":"user",
            "content": user_input
        }
    ]
    while True:        
        response = client.chat.completions.parse(
            model = "gpt-4o",
            response_format = PromptOutput,
            messages=message_chat
        )
        # print(response.choices[0].message.content)
        # msg_resp = json.loads(response.choices[0].message.content)
        # print(type(msg_resp))
        msg_resp = response.choices[0].message.parsed
        print(msg_resp)
        break
