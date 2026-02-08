import os
import json
from prefect import task, flow
from generate_mails import save_as_json
from generate_html import save_as_html
from generate_news import generate
from delivery_email import send_newsletter_email

@task(name="Fetch News", retries=2, retry_delay_seconds=60)
def fetch_news_task(time_frame: int, load_from_cache: bool):
    """Prefect task to either generate fresh news or load from cache."""
    result = None
    if load_from_cache:
        print("📁 Loading news from cache (news_report.json)...")
        try:
            with open("news_report.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                result = data.get("content")
        except FileNotFoundError:
            print("❌ news_report.json not found. Falling back to AI generation.")
            load_from_cache = False
            
    if not load_from_cache or not result:
        result = generate(time_frame)
    
    return result, load_from_cache

@task(name="Save Data Archive")
def save_data_task(result, load_from_cache: bool):
    """Saves news content to JSON if newly generated."""
    if not load_from_cache:
        save_as_json(result)
    return True

@task(name="Generate HTML Newsletter")
def generate_html_task(result):
    """Converts news content to styled HTML."""
    return save_as_html(result, return_content=True)

@task(name="Deliver Newsletter", retries=3, retry_delay_seconds=300)
def deliver_newsletter_task(html_content, recipient_emails):
    """Sends the newsletter via email to one or more addresses."""
    if recipient_emails:
        return send_newsletter_email(html_content, recipient_emails)
    return False

@flow(name="AI Newsletter Orchestrator")
def newsletter_flow(
    time_frame: int = 7, 
    load_from_cache: bool = False, 
    recipient_emails: list = ["shubhamgoel386@gmail.com"]
):
    """
    Main flow to orchestrate the AI Newsletter delivery.
    
    Parameters:
    - time_frame: Number of days to look back for news.
    - load_from_cache: If True, uses existing news_report.json.
    - recipient_emails: List of email addresses or a single comma-separated string.
    """
    # 1. Fetch news
    result, cached = fetch_news_task(time_frame, load_from_cache)
    
    if not result:
        raise ValueError("Failed to obtain news content.")
        
    # 2. Archive 
    save_data_task(result, cached)
    
    # 3. Generate Design
    html_content = generate_html_task(result)
    
    # 4. Deliver to all recipients
    deliver_newsletter_task(html_content, recipient_emails)

if __name__ == "__main__":
    # Local execution for testing with environment variables as defaults
    env_recipients = os.getenv("RECIPIENT_EMAIL", "shubhamgoel386@gmail.com").split(",")
    
    newsletter_flow(
        time_frame=int(os.getenv("TIME_FRAME", "7")),
        load_from_cache=os.getenv("LOAD_FROM_CACHE", "false").lower() == "true",
        recipient_emails=env_recipients
    )
