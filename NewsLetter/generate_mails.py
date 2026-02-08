import os
import json

def save_as_json(content, filename="news_report.json"):
    """Saves the news content as a JSON file."""
    data = {
        "title": "AI & Tech News Brief",
        "content": content,
        "generated_at": str(os.popen("date").read().strip())
    }
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    print(f"Successfully saved news to {filename}")