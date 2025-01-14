from typing import Tuple
import urllib.parse
import requests

BASE_AUTH_URL = "https://accounts.spotify.com/authorize"
CLIENT_ID = "<>"
REDIRECT_URI = "<>"
SCOPES = [
    "user-read-playback-position",
]

query_params = {
    "client_id": CLIENT_ID,
    "response_type": "code",
    "redirect_uri": REDIRECT_URI,
    "scope": " ".join(SCOPES),
    "show_dialog": "true"
}

auth_url = f"{BASE_AUTH_URL}?{urllib.parse.urlencode(query_params)}"


def get_access_token(code: str) -> Tuple[str, str]:
    url = "https://accounts.spotify.com/api/token"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": "<YOUR_CLIENT_SECRET>"
    }
    
    response = requests.post(url, data=data)
    response.raise_for_status()
    token_info = response.json()

    access_token = token_info["access_token"]
    refresh_token = token_info["refresh_token"]
    return access_token, refresh_token

# headers = {
#     "Authorization": f"Bearer {access_token}",
#     "Content-Type": "application/json"
# }

# response = requests.get("https://api.spotify.com/v1/me/player", headers=headers)

def refresh_access_token(refresh_token: str) -> str:
    url = "https://accounts.spotify.com/api/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": CLIENT_ID,
        "client_secret": "<YOUR_CLIENT_SECRET>",
    }
    
    response = requests.post(url, data=data)
    response.raise_for_status()
    token_info = response.json()
    
    new_access_token = token_info["access_token"]
    return new_access_token
