import os
from datetime import datetime, timedelta, timezone
from google import genai
from google.genai import types
from dotenv import load_dotenv
from prompt import get_master_prompt

load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_KEY")

def generate(timeframe_days=7):
    """Generate news content using Gemini API with streaming.
    
    Args:
        timeframe_days (int): Number of days to look back for news (default: 7)
    
    Returns:
        str: Generated news content
    """
    client = genai.Client(
        api_key=GEMINI_KEY,
    )

    model = "gemini-2.5-flash"
    
    # Get the master prompt with the specified timeframe
    prompt = get_master_prompt(timeframe_days)

    now = datetime.now(timezone.utc)

    time_range_start = (now - timedelta(days=timeframe_days)).replace(microsecond=0)
    time_range_end = (now + timedelta(days=1)).replace(microsecond=0)

    time_range = types.Interval(
        start_time=time_range_start,
        end_time=time_range_end
        )
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
            time_range_filter=time_range
        )),
    ]
    generate_content_config = types.GenerateContentConfig(
        temperature=1,
        tools=tools,
    )

    print("Generating news content...")
    
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
