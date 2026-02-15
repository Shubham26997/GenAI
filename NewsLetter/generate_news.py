from google import genai
from google.genai import types
from prompt import get_master_prompt

def generate(timeframe_days=7):
    """Generate news content using Gemini API with streaming.
    
    Args:
        timeframe_days (int): Number of days to look back for news (default: 7)
    
    Returns:
        str: Generated news content
    """
    client = genai.Client(
        api_key="",
    )

    model = "gemini-2.5-flash"
    
    # Get the master prompt with the specified timeframe
    prompt = get_master_prompt(timeframe_days)
    
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
