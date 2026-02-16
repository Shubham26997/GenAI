import os
from dotenv import load_dotenv
from fastapi import FastAPI
from generate_post import generate
from linkedin_poster import post_to_social
from get_my_id import get_linkedin_person_id
from models import PromptPara
load_dotenv()
LINKEDIN_ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN")

app = FastAPI(
    title="LinkedIn Post Automate"
)
@app.get("/")
async def home():
    return "Welcome to Fastapi"

@app.post("/post_linkedin/")
async def post_to_linkedin(core_problem: str, tech_compare: str, app_context: str, is_technical: bool=False):
    print("Hi Linked IN we are here to explore")
    content_linkedin = generate(
        core_problem=core_problem,
        tech_compare=tech_compare,
        app_context=app_context,
        is_technical=is_technical
    )
    # my_person_id = get_linkedin_person_id(LINKEDIN_ACCESS_TOKEN)
    # result = post_to_social(content_linkedin, LINKEDIN_ACCESS_TOKEN, my_person_id)
    # print(result)
    print(content_linkedin)
    return "Post created on LinkedIN"
    # print(content_linkedin)