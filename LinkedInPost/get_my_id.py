import requests
from constant import LINKEDIN_ACCESS_TOKEN

def get_linkedin_person_id(access_token):
    """
    Fetches the profile info to retrieve the Person ID (URN).
    Since you have 'openid' and 'profile' scopes, we use the OIDC endpoint.
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
    }
    
    # Try the OIDC UserInfo endpoint (matches your scopes)
    url = "https://api.linkedin.com/v2/userinfo"
    
    try:
        print(f"Requesting ID from {url}...")
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            # The 'sub' field contains the member ID string
            member_id = data.get('sub')
            if member_id:
                person_id = f"urn:li:person:{member_id}"
                print(f"SUCCESS! Found Person ID: {person_id}")
                return person_id
        else:
            print(f"OIDC Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Exception during ID retrieval: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"API Response: {e.response.text}")
        return None

    print("\nHELP: Since you have 'openid' and 'profile' scopes, ensure your token was")
    print("generated with 'w_member_social' AND 'openid' AND 'profile'.")
    return None

if __name__ == "__main__":
    if LINKEDIN_ACCESS_TOKEN and LINKEDIN_ACCESS_TOKEN != "YOUR_LINKEDIN_ACCESS_TOKEN":
        get_linkedin_person_id(LINKEDIN_ACCESS_TOKEN)
    else:
        print("Error: Missing valid LINKEDIN_ACCESS_TOKEN in constant.py")
