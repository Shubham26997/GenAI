import requests
import json

def post_to_linkedin(content, access_token, author_id):
    """
    Posts a text share to LinkedIn using the UGC (User Generated Content) API.
    
    Args:
        content (str): The text content to post.
        access_token (str): LinkedIn OAuth 2.0 access token.
        author_id (str): LinkedIn Member ID (format: 'urn:li:person:ID').
        
    Returns:
        dict: API response JSON or error details.
    """
    url = "https://api.linkedin.com/v2/ugcPosts"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0"
    }
    
    payload = {
        "author": author_id,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": content
                },
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        return {
            "status": "success",
            "data": response.json() if response.text else "Post created successfully"
        }
    except requests.exceptions.HTTPError as e:
        return {
            "status": "error",
            "message": f"HTTP Error: {e}",
            "response": response.text
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
