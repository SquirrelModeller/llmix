from abc import abstractmethod
from typing import List, Optional
from src.music.components import Track, Artist, Album

class BaseMusic():

    @abstractmethod
    def search_tracks(self, query: str, limit: int = 20) -> List[Track]:
        """Search for tracks"""

    @abstractmethod
    def get_track(self, track_id: str) -> Optional[Track]:
        """Get a specific track by ID"""

    @abstractmethod
    def get_artist(self, artist_id: str) -> Optional[Artist]:
        """Get a specific artist by ID"""

    def get_song(self, name: str, artist: str, year: str) -> str:
        """Retrieve a specific song"""

    def play_song(self, song) -> None:
        """Play a song"""

    def stop_music(self) -> None:
        """Stop the music"""

    def get_current_playlist(self) -> dict:
        """Get the current playlist which is playing"""

    def queue_song(self, song) -> None:
        """Queue a song"""

    def insert_song_in_playlist(self, song, position) -> None:
        """Insert a song into the playlist"""

    def set_volume(self, vol):
        """Set the volume"""
        # Set as median of all votes
