from abc import abstractmethod
from typing import List, Optional, Dict
from src.music.components import Track, Artist, User, UserToken

class BaseMusic():

    @abstractmethod
    def search_tracks(self, query: str, limit: int = 20) -> List[Track]:
        """
        Search for tracks
        
        Args:
            query (str): The parameter which is utilized to performing the search
            limit (int): A limit to the maximum search results returned
        
        Returns:
            List[Track]: A list of tracks from the search
        """

    @abstractmethod
    def get_track(self, track_id: str) -> Optional[Track]:
        """
        Get a specific track by ID
        
        Args:
            track_id (str): THe id of a track of a song respective to the provider

        Returns:
            Optional[Track]: Information regarding the song
        """

    @abstractmethod
    def get_artist(self, artist_id: str) -> Optional[Artist]:
        """
        Get a specific artist by ID
        
        Args:
            artist_id (str): The id of an artist respective to the provider

        Returns:
            Optional[Artist]: Information regarding the artist
        """

    @abstractmethod
    def request_user_token(self) -> UserToken:
        """
        Opens localhost server and requests permissions.
        Establishes and retrieves user token.

        Returns:
            UserToken: An objecct containing the website, access- refresh-tokens and expiry date  
        """

    @abstractmethod
    def get_user_playlists(self, user: User) -> List[Dict]:
        """
        Get all playlists for a given user.
        
        Args:
            user (User): The user whose playlists to retrieve
            
        Returns:
            List[Dict]: List of playlist objects containing id, name, and tracks
        """

    @abstractmethod
    def create_playlist(
        self, user: User,
        name: str,
        description: str = "",
        public: bool = True
    ) -> Dict:
        """
        Create a new playlist for a user.
        
        Args:
            user (User): The user to create the playlist for
            name (str): Name of the playlist
            description (str): Optional description of the playlist
            public (bool): Whether the playlist should be public
            
        Returns:
            Dict: The created playlist object
        """

    @abstractmethod
    def add_tracks_to_playlist(self, user: User, playlist_id: str, track_uris: List[str]) -> None:
        """
        Add tracks to a user's playlist.
        
        Args:
            user (User): The user who owns the playlist
            playlist_id (str): ID of the playlist to add tracks to
            track_uris (List[str]): List of Spotify track URIs to add
            
        Returns:
            None
        """
    
    @abstractmethod
    def reorder_playlist_tracks(
        self, user: User,
        playlist_id: str,
        range_start: int,
        insert_before: int,
        range_length: int = 1
    ) -> None:
        """
        Reorder tracks in a user's playlist.
        
        Args:
            user (User): The user who owns the playlist
            playlist_id (str): ID of the playlist to reorder
            range_start (int): Position of first track to reorder
            insert_before (int): Position where tracks should be inserted
            range_length (int): Number of tracks to reorder
            
        Returns:
            None
        """

    @abstractmethod
    def play_user_playlist(
        self, user: User,
        playlist_id: str,
        device_id: Optional[str] = None
    ) -> None:
        """
        Start playing a user's playlist on their active device.
        
        Args:
            user (User): The user who wants to play the playlist
            playlist_id (str): ID of the playlist to play
            device_id (Optional[str]): Specific device to play on, if None uses active device
            
        Returns:
            None
        """

    @abstractmethod
    def pause_playback(self, user: User, device_id: Optional[str] = None) -> None:
        """
        Pause the user's current playback.
        
        Args:
            user (User): The user whose playback to pause
            device_id (Optional[str]): Specific device to pause on, if None uses active device
            
        Returns:
            None
        """

    @abstractmethod
    def get_user_information(self, user: User) -> Dict:
        """
        Get information about the user

        Args:
            user (User): The user
        
        Returns:
            Dict: Information regarding the user
        """

    @abstractmethod
    def set_playlist_track_order(self, user: User, playlist_id: str, track_sequence: List[str], insert_at_track: str) -> None:
        """
        Reorders tracks in a playlist to match the specified sequence, inserting them at the specified track.
        
        Args:
            user (User): The user who owns the playlist
            playlist_id (str): The ID of the playlist to modify
            track_sequence (List[str]): List of track IDs in the desired order
            insert_at_track (str): Track ID where the sequence should be inserted
        """

    @abstractmethod
    def get_user_playlist(self, user: User, track_id: str) -> Dict:
        """
        Fetches a users playlist

        Args:
            user (User): The user who owns the playlist
            track_id (str): The id of the playlist being fetched

        Returns:
            Dict: Information regarding the playlist
        """
