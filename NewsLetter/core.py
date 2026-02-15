import os
import re
import json
from dotenv import load_dotenv
from generate_mails import save_as_json
from generate_html import save_as_html
from generate_news import generate
from delivery_email import send_newsletter_email

load_dotenv()
if __name__ == "__main__":
    time_frame = int(os.getenv("TIME_FRAME", "7"))
    load_from_cache = os.getenv("LOAD_FROM_CACHE", "false").lower() == "true"
    
    result = None
    
    if load_from_cache:
        print("📁 Loading news from cache (news_report.json)...")
        try:
            with open("news_report.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                result = data.get("content")
                if not result:
                    print("⚠️ Cache file empty or missing 'content' key.")
        except FileNotFoundError:
            print("❌ news_report.json not found. Falling back to AI generation.")
            load_from_cache = False
    
    if not load_from_cache:
        result = generate(time_frame)
    
    if result:
        save_as_html(result)
        # Only save JSON if we generated new content (or if it was missing)
        if not load_from_cache:
            save_as_json(result)
            
        print(f"\n✅ Newsletter {'loaded' if load_from_cache else 'generated'} successfully!")
        
        # Delivery Options
        recipient_email = os.getenv("RECIPIENT_EMAIL", "shubhamgoel386@gmail.com")
        if recipient_email:
            send_newsletter_email(save_as_html(result, return_content=True), recipient_email)
            
    else:
        print("❌ Failed to obtain news content.")
