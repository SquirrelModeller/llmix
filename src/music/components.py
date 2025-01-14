from typing import List, Optional, Set
from enum import Enum, auto
from uuid import UUID
from datetime import datetime
from dataclasses import dataclass

class Permission(Enum):
    EDIT_QUEUE = auto()
    CONTROL_PLAYBACK = auto()
    CONTROL_VOLUME = auto()
    MANAGE_PLAYLISTS = auto()
    ADMIN = auto()

@dataclass
class User:
    """Represents a user in the music system"""
    user_id: UUID
    username: str
    display_name: str
    permissions: Set[Permission]
    created_at: datetime
    last_active: datetime
    is_active: bool = True

@dataclass
class Artist:
    """Represents a music artist"""
    artist_id: str
    name: str
    genres: List[str]
    image_url: Optional[str] = None

@dataclass
class Track:
    """Represents a music track"""
    track_id: str
    title: str
    artist: Artist
    duration_ms: int
    album: Optional['Album'] = None
    explicit: bool = False
    preview_url: Optional[str] = None
    external_url: Optional[str] = None
    popularity: Optional[int] = None
    is_playable: bool = True

@dataclass
class Album:
    """Represents a music album"""
    album_id: str
    title: str
    artist: Artist
    release_date: datetime
    tracks: List[Track]
    album_type: str
    total_tracks: int
    image_url: Optional[str] = None
    genres: List[str] = None

@dataclass
class PlaybackState:
    """Represents the current playback state"""
    is_playing: bool
    position_ms: int
    volume_percent: int
    repeat_mode: str
    shuffle_mode: bool

@dataclass
class QueueItem:
    """Represents an item in the playback queue"""
    track: Track
    requested_by: User
    requested_at: datetime
    votes: Set[UUID]
    position: int
