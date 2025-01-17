import logging
from typing import List, Optional, Dict, TypeVar, Callable, Any
from datetime import datetime, timedelta
import functools
import requests
from src.music.components import Track, Artist, Album, UserToken, User
from src.music.base_music import BaseMusic
from src.config.settings import SpotifySettings
from src.music.auth.oauth2_server import OAuth2Server

logger = logging.getLogger(__name__)

T = TypeVar('T')

class SpotifyProvider(BaseMusic):
    """Spotify music provider implementation"""

    BASE_URL = "https://api.spotify.com/v1"
    AUTH_URL = "https://accounts.spotify.com/api/token"

    def __init__(self, settings: SpotifySettings):
        self.settings = settings
        self._access_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None

    def _ensure_token(self):
        """Ensures a valid access token is available"""
        if not self._access_token or not self._token_expiry or datetime.now() >= self._token_expiry:
            self._refresh_token()

    def _refresh_token(self):
        """Refreshes the Spotify access token"""
        data = {
            "grant_type": "client_credentials",
            "client_id": self.settings.client_id,
            "client_secret": self.settings.client_secret
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        try:
            response = requests.post(
                self.AUTH_URL,
                data=data,
                headers=headers,
                timeout=10
            )

            response.raise_for_status()
            token_data = response.json()

            self._access_token = token_data["access_token"]
            self._token_expiry = datetime.now() + timedelta(seconds=token_data["expires_in"])

            logger.debug("Successfully refreshed Spotify access token")

        except requests.exceptions.HTTPError as http_err:
            logger.error(f"HTTP error during token refresh: {http_err.response.text}")
            raise
        except requests.exceptions.RequestException as req_err:
            logger.error(f"Request failed during token refresh: {str(req_err)}")
            raise
        except KeyError as key_err:
            logger.error(f"Unexpected response format: {str(key_err)}")
            raise ValueError("Invalid response format from Spotify auth server")

    def _get_headers(self, user: Optional[User] = None) -> Dict[str, str]:
        """Returns headers for Spotify API requests"""
        if user and 'spotify' in user.connections:
            token = user.connections['spotify'].access_token
        else:
            self._ensure_token()
            token = self._access_token

        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    def _make_request(
        self,
        method: str,
        url: str,
        user: Optional[User] = None,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        auth_required: bool = True
    ) -> Dict:
        """Generic method to make HTTP requests to Spotify API"""
        try:
            request_headers = headers or {}
            if auth_required:
                request_headers.update(self._get_headers(user))

            response = requests.request(
                method,
                url,
                headers=request_headers,
                params=params,
                json=data if headers and "application/json" in headers["Content-Type"] else data,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Spotify API request failed: {str(e)}")
            raise

    @staticmethod
    def _require_user_connection(func: Callable) -> Callable:
        """Decorator to check if user has Spotify connection"""
        @functools.wraps(func)
        def wrapper(self, user: User, *args, **kwargs):
            if 'spotify' not in user.connections:
                raise ValueError("User does not have a Spotify connection")
            return func(self, user, *args, **kwargs)
        return wrapper

    def _create_artist(self, artist_data: Dict) -> Artist:
        """Helper method to create Artist object from API response"""
        return Artist(
            artist_id=artist_data["id"],
            name=artist_data["name"],
            genres=artist_data.get("genres", []),
            image_url=artist_data.get("images", [{}])[0].get("url")
        )

    def _create_album(self, album_data: Dict, artist: Artist) -> Album:
        """Helper method to create Album object from API response"""
        return Album(
            album_id=album_data["id"],
            title=album_data["name"],
            artist=artist,
            release_date=datetime.now(),  # TODO: date is incorrect but spotify has a weird dating system
            tracks=[],
            album_type=album_data["album_type"],
            total_tracks=album_data["total_tracks"],
            image_url=album_data.get("images", [{}])[0].get("url")
        )

    def _create_track(self, track_data: Dict) -> Track:
        """Helper method to create Track object from API response"""
        artist = self._create_artist(track_data["artists"][0])
        album = self._create_album(track_data["album"], artist)


        return Track(
            track_id=track_data["id"],
            title=track_data["name"],
            artist=artist,
            duration_ms=track_data["duration_ms"],
            uri=track_data["uri"],
            album=album,
            explicit=track_data["explicit"],
            preview_url=track_data["preview_url"],
            external_url=track_data["external_urls"]["spotify"],
            popularity=track_data["popularity"],
            is_playable=not track_data.get("is_local", False)
        )

    def request_user_token(self) -> UserToken:
        spotify_auth_template = (
            "https://accounts.spotify.com/authorize"
            "?client_id=$client_id"
            "&response_type=code"
            "&redirect_uri=$redirect_uri"
            "&scope=user-read-playback-state%20playlist-modify-public%20playlist-modify-private%20user-read-private"
        )

        auth_server = OAuth2Server(
            client_id=self.settings.client_id,
            client_secret=self.settings.client_secret,
            auth_url_template=spotify_auth_template,
            token_url=self.AUTH_URL
        )

        try:
            tokens = auth_server.get_auth_tokens()
            token_expiry = datetime.now() + timedelta(seconds=tokens.get("expires_in"))
            return UserToken(
                website="spotify",
                access_token=tokens.get("access_token"),
                refresh_token=tokens.get("refresh_token"),
                token_expiry=token_expiry
            )
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            raise

    def search_tracks(self, query: str, limit: int = 20) -> List[Track]:
        response = self._make_request(
            "GET",
            f"{self.BASE_URL}/search",
            params={"q": query, "type": "track", "limit": limit}
        )

        return [self._create_track(item) for item in response["tracks"]["items"]]

    def get_track(self, track_id: str) -> Optional[Track]:
        try:
            response = self._make_request("GET", f"{self.BASE_URL}/tracks/{track_id}")
            return self._create_track(response)
        except Exception:
            return None

    def get_artist(self, artist_id: str) -> Optional[Artist]:
        try:
            response = self._make_request("GET", f"{self.BASE_URL}/artists/{artist_id}")
            return self._create_artist(response)
        except Exception:
            return None

    @_require_user_connection
    def get_user_information(self, user: User) -> Dict:
        return self._make_request("GET", f"{self.BASE_URL}/me", user=user)

    @_require_user_connection
    def get_user_playlists(self, user: User) -> List[Dict]:
        response = self._make_request("GET", f"{self.BASE_URL}/me/playlists", user=user)
        return response["items"]
    
    @_require_user_connection
    def get_user_playlist(self, user: User, track_id: str) -> Dict:
        response = self._make_request("GET", f"{self.BASE_URL}/playlists/{track_id}", user=user)
        return response

    @_require_user_connection
    def create_playlist(self, user: User, name: str, description: str = "", public: bool = True) -> Dict:
        user_id = user.connections['spotify'].info['id']
        data = {"name": name, "description": description, "public": public}
        return self._make_request(
            "POST",
            f"{self.BASE_URL}/users/{user_id}/playlists",
            user=user,
            data=data
        )

    @_require_user_connection
    def add_tracks_to_playlist(self, user: User, playlist_id: str, track_uris: List[str]) -> None:
        url = f"{self.BASE_URL}/playlists/{playlist_id}/tracks"

        for i in range(0, len(track_uris), 100):
            chunk = track_uris[i:i + 100]
            self._make_request("POST", url, user=user, data={"uris": chunk})

    @_require_user_connection
    def reorder_playlist_tracks(
        self,
        user: User,
        playlist_id: str,
        range_start: int,
        insert_before: int,
        range_length: int = 1
    ) -> None:
        data = {
            "range_start": range_start,
            "insert_before": insert_before,
            "range_length": range_length
        }
        self._make_request(
            "PUT",
            f"{self.BASE_URL}/playlists/{playlist_id}/tracks",
            user=user,
            data=data
        )

    @_require_user_connection
    def play_user_playlist(self, user: User, playlist_id: str, device_id: Optional[str] = None) -> None:
        url = f"{self.BASE_URL}/me/player/play"
        if device_id:
            url += f"?device_id={device_id}"

        data = {"context_uri": f"spotify:playlist:{playlist_id}"}
        self._make_request("PUT", url, user=user, data=data)

    @_require_user_connection
    def pause_playback(self, user: User, device_id: Optional[str] = None) -> None:
        url = f"{self.BASE_URL}/me/player/pause"
        if device_id:
            url += f"?device_id={device_id}"

        self._make_request("PUT", url, user=user)
