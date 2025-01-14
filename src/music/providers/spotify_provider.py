import requests
import logging
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from src.music.components import Track, Artist, Album
from src.music.base_music import BaseMusic
from src.config.settings import SpotifySettings

logger = logging.getLogger(__name__)

class SpotifyProvider(BaseMusic):
    """Spotify music provider implementation"""
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
        url = "https://accounts.spotify.com/api/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "grant_type": "client_credentials",
            "client_id": self.settings.client_id,
            "client_secret": self.settings.client_secret
        }

        try:
            response = requests.post(url, headers=headers, data=data, timeout=10)
            response.raise_for_status()
            token_data = response.json()
            
            self._access_token = token_data["access_token"]
            
            self._token_expiry = datetime.now() + timedelta(seconds=token_data["expires_in"])
        except Exception as e:
            logger.error(f"Failed to refresh Spotify token: {str(e)}")
            raise

    def _get_headers(self) -> Dict[str, str]:
        """Returns headers for Spotify API requests"""
        self._ensure_token()
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json"
        }

    def search_tracks(self, query: str, limit: int = 20) -> List[Track]:
        url = "https://api.spotify.com/v1/search"
        params = {
            "q": query,
            "type": "track",
            "limit": limit
        }

        try:
            response = requests.get(url, headers=self._get_headers(), params=params)
            response.raise_for_status()
            data = response.json()

            tracks = []
            for item in data["tracks"]["items"]:
                artist = Artist(
                    artist_id=item["artists"][0]["id"],
                    name=item["artists"][0]["name"],
                    genres=[]
                )

                album = Album(
                    album_id=item["album"]["id"],
                    title=item["album"]["name"],
                    artist=artist,
                    release_date=datetime.now(), #datetime.strptime(f"{item['album']['release_date']}-1-1", "%Y-%m-%d")
                    tracks=[],
                    album_type=item["album"]["album_type"],
                    total_tracks=item["album"]["total_tracks"],
                    image_url=item["album"]["images"][0]["url"] if item["album"]["images"] else None
                )

                track = Track(
                    track_id=item["id"],
                    title=item["name"],
                    artist=artist,
                    duration_ms=item["duration_ms"],
                    album=album,
                    explicit=item["explicit"],
                    preview_url=item["preview_url"],
                    external_url=item["external_urls"]["spotify"],
                    popularity=item["popularity"],
                    is_playable=not item["is_local"]
                )
                tracks.append(track)

            return tracks
        except Exception as e:
            logger.error(f"Failed to search tracks: {str(e)}")
            raise

    def get_track(self, track_id: str) -> Optional[Track]:
        url = f"https://api.spotify.com/v1/tracks/{track_id}"

        try:
            response = requests.get(url, headers=self._get_headers())
            response.raise_for_status()
            item = response.json()

            artist = Artist(
                artist_id=item["artists"][0]["id"],
                name=item["artists"][0]["name"],
                genres=[]
            )

            album = Album(
                album_id=item["album"]["id"],
                title=item["album"]["name"],
                artist=artist,
                release_date=datetime.now(), #datetime.strptime(item["album"]["release_date"], "%Y-%m-%d")
                tracks=[],
                album_type=item["album"]["album_type"],
                total_tracks=item["album"]["total_tracks"],
                image_url=item["album"]["images"][0]["url"] if item["album"]["images"] else None
            )

            return Track(
                track_id=item["id"],
                title=item["name"],
                artist=artist,
                duration_ms=item["duration_ms"],
                album=album,
                explicit=item["explicit"],
                preview_url=item["preview_url"],
                external_url=item["external_urls"]["spotify"],
                popularity=item["popularity"],
                is_playable=not item["is_local"]
            )
        except Exception as e:
            logger.error(f"Failed to get track {track_id}: {str(e)}")
            return None

    def get_artist(self, artist_id: str) -> Optional[Artist]:
        url = f"https://api.spotify.com/v1/artists/{artist_id}"

        try:
            response = requests.get(url, headers=self._get_headers())
            response.raise_for_status()
            item = response.json()

            return Artist(
                artist_id=item["id"],
                name=item["name"],
                genres=item["genres"],
                image_url=item["images"][0]["url"] if item["images"] else None
            )
        except Exception as e:
            logger.error(f"Failed to get artist {artist_id}: {str(e)}")
            return None
