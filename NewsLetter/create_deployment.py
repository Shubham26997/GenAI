import os
import time
import urllib.request
import prefect
from flow_newsletter import newsletter_flow

def wait_for_prefect_api(url, timeout=90):
    """Wait for the Prefect API to become available."""
    print(f"⏳ Waiting for Prefect API at {url}...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            # Check the health endpoint
            with urllib.request.urlopen(f"{url}/health") as response:
                if response.status == 200:
                    print("✅ Prefect API is ready!")
                    return True
        except Exception as e:
            # print(f"DEBUG: Still waiting... ({e})")
            pass
        time.sleep(3)
    print("❌ Timeout waiting for Prefect API.")
    return False

def deploy_newsletter():
    """
    Deploys multiple instances of the newsletter flow to Prefect.
    This uses the modern 'prefect.serve' method to run multiple deployments concurrently.
    """
    
    # 0. Wait for API availability
    # We use a longer timeout and better retry logic
    api_url = os.getenv("PREFECT_API_URL", "http://server:4200/api")
    if not wait_for_prefect_api(api_url):
        print("⚠️ Proceeding despite API timeout (Prefect might still be starting)...")
    
    # Define parameters from Environment as defaults
    env_recipients = os.getenv("RECIPIENT_EMAIL", "shubhamgoel386@gmail.com").split(",")
    
    print("🚀 Starting Prefect Multi-Flow Service...")

    # 1. Define the Weekly Deployment
    weekly_dep = newsletter_flow.to_deployment(
        name="weekly-service",
        description="Weekly AI & Tech Newsletter - Every Sunday at 9 AM.",
        tags=["production", "Weekly", "newsletter"],
        parameters={
            "time_frame": 7,
            "load_from_cache": False,
            "recipient_emails": env_recipients
        },
        cron="0 9 * * 0", # Every Sunday at 9 AM
        timezone="Asia/Kolkata"
    )

    # 2. Define the Manual/One-time Deployment
    manual_dep = newsletter_flow.to_deployment(
        name="manual-service",
        description="On-demand AI & Tech Newsletter delivery.",
        tags=["production", "One-time", "newsletter"],
        parameters={
            "time_frame": 7,
            "load_from_cache": False,
            "recipient_emails": env_recipients
        },
        timezone="Asia/Kolkata"
    )

    # 3. Serve both concurrently
    print("📡 Serving deployments to Prefect Dashboard...")
    prefect.serve(weekly_dep, manual_dep)

if __name__ == "__main__":
    deploy_newsletter()
