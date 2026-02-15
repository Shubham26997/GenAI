import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from prompt import get_master_prompt

load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_KEY")

def generate(core_problem, tech_compare, app_context):
    """Generate LinkedIn content using Gemini API with streaming.
    
    Args:
        core_problem (str): Main core problem of linked in post
        tech_compare (str): Two techs which will get compare in the post
        app_context (str): Application context overall based on the post is created
    Returns:
        str: Generated post content
    """
    client = genai.Client(
        api_key=GEMINI_KEY,
    )

    model = "gemini-2.5-flash"
    
    # Get the master prompt with the specified timeframe
    prompt = get_master_prompt(core_problem, tech_compare, app_context)
    
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=prompt),
            ],
        ),
    ]
    tools = [
        types.Tool(googleSearch=types.GoogleSearch(
        )),
    ]
    generate_content_config = types.GenerateContentConfig(
        temperature=1,
        tools=tools,
    )

    print("Generating Linkedin content...")
    
    # Use a list to collect chunks for better performance
    news_chunks = []
    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        if chunk.text:
            news_chunks.append(chunk.text)
    
    # Join all chunks into final output
    return ''.join(news_chunks)
