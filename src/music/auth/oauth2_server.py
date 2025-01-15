import http.server
import socketserver
import urllib.parse as urlparse
import os
import webbrowser
from threading import Thread
from typing import Optional, Dict
from string import Template
import requests

class OAuth2Server:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        auth_url_template: str,
        token_url: str,
        port: int = 8888
    ):
        """
        Initialize OAuth2
        
        Args:
            client_id: OAuth client ID
            client_secret: OAuth client secret
            auth_url_template: Authorization URL template
            token_url: URL for token exchange
            port: Port to run local server on
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.port = port
        self.redirect_uri = f"http://localhost:{port}/callback"
        self.auth_url_template = auth_url_template
        self.token_url = token_url
        self.auth_tokens: Optional[Dict] = None
        self.server: Optional[socketserver.TCPServer] = None

    class _OAuthHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            self.auth_tokens = None
            super().__init__(*args, **kwargs)

        def do_GET(self):
            parsed_path = urlparse.urlparse(self.path)

            if parsed_path.path == "/callback":
                query_params = urlparse.parse_qs(parsed_path.query)
                code = query_params.get("code", [None])[0]

                if code:
                    token_data = {
                        "grant_type": "authorization_code",
                        "code": code,
                        "redirect_uri": self.server.oauth_instance.redirect_uri,
                        "client_id": self.server.oauth_instance.client_id,
                        "client_secret": self.server.oauth_instance.client_secret
                    }

                    r = requests.post(self.server.oauth_instance.token_url, data=token_data)

                    if r.status_code == 200:
                        self.server.oauth_instance.auth_tokens = r.json()
                        self.send_response(200)
                        self.end_headers()
                        self.wfile.write(b"Authentication successful! You can close this window.")

                        Thread(target=self.server.shutdown).start()
                    else:
                        self.send_response(400)
                        self.end_headers()
                        self.wfile.write(b"Token request failed.")
                else:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b"No code parameter found.")
            else:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"OAuth2 authentication running.")

        def log_message(self, format, *args):
            pass

    def get_auth_tokens(self) -> Dict:
        """
        Start the authentication server and return the tokens once obtained.
        
        Returns:
            Dict containing access_token, refresh_token, and expires_in
        """

        self.server = socketserver.TCPServer(("", self.port), self._OAuthHandler)
        self.server.oauth_instance = self


        server_thread = Thread(target=self.server.serve_forever)
        server_thread.daemon = True
        server_thread.start()


        template = Template(self.auth_url_template)
        auth_url = template.substitute(
            client_id=self.client_id,
            redirect_uri=urlparse.quote(self.redirect_uri)
        )

        webbrowser.open(auth_url)

        server_thread.join()

        if self.auth_tokens is None:
            raise Exception("Failed to obtain authentication tokens")

        return self.auth_tokens


if __name__ == "__main__":
    spotify_auth_template = (
        "https://accounts.spotify.com/authorize"
        "?client_id=$client_id"
        "&response_type=code"
        "&redirect_uri=$redirect_uri"
        "&scope=user-read-playback-state"
    )
    spotify_token_url = "https://accounts.spotify.com/api/token"

    auth_server = OAuth2Server(
        client_id=os.environ.get("SPOTIFY_CLIENT_ID"),
        client_secret=os.environ.get("SPOTIFY_CLIENT_SECRET"),
        auth_url_template=spotify_auth_template,
        token_url=spotify_token_url
    )

    try:
        tokens = auth_server.get_auth_tokens()

        print(f"Access Token: {tokens.get('access_token')}")
        print(f"Refresh Token: {tokens.get('refresh_token')}")
        print(f"Expires In: {tokens.get('expires_in')}")
    except Exception as e:
        print(f"Authentication failed: {e}")
