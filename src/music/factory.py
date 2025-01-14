import os
from src.config.settings import MusicConfig
from src.music.providers.spotify_provider import SpotifyProvider

class MusicFactory:
    @staticmethod
    def create(config: MusicConfig):
        if config.provider == "spotify":
            if (config.spotify.client_id and config.spotify.client_secret):
                return SpotifyProvider(config.spotify)

            client = os.environ.get("SPOTIFY_CLIENT_ID")
            secret = os.environ.get("SPOTIFY_CLIENT_SECRET")
            config.spotify.client_id = client
            config.spotify.client_secret = secret

            return SpotifyProvider(config.spotify)

