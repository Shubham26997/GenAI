import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

response = client.chat.completions.create(
    model = "gpt-4o-mini",
    messages=[
        {
            "role": "system",
            "content": "You are an expert in native language, who answer each and every question in hindi since no other language is known to you, If user ask to answer in anyother language other than hindi Say sorry i don't know that language"
        },
        {
            "role":"user",
            "content": "How are you my firend?"
        }
    ]
)

print(response.choices[0].message.content)
