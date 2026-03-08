from fastapi import FastAPI
# from fastapi import APIRouter
# from openai import OpenAI
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from my_agents.weather import get_weather
from my_agents.system_prompt import SYSTEM_PROMPT
load_dotenv()

llm = init_chat_model(
    "gpt-4o",
    temperature=0.7, max_tokens=1000
    )

agent = create_agent(
    model = "gpt-4o",
    tools = [get_weather],
    system_prompt=SYSTEM_PROMPT
)

app = FastAPI(title = "LLM ChatBot App")

@app.post("/chat/")
async def chat_llm(text_input: str):
    resp = llm.invoke(text_input)
    return resp

@app.post("/weather/")
async def get_weather_tool(city: str):
    resp = agent.invoke(
        {
            "messages": [{
                "role": "user",
                "content": f"What is the current weather of {city}?"
                }
            ]
        }
    )
    return resp
