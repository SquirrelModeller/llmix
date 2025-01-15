from typing import List, Optional, Set, Dict, Any
from datetime import datetime
from enum import Enum, auto
from uuid import UUID
from dataclasses import dataclass, field
import bcrypt


class Permission(Enum):
    """Represents various system permissions"""
    EDIT_QUEUE = auto()
    CONTROL_PLAYBACK = auto()
    CONTROL_VOLUME = auto()
    MANAGE_PLAYLISTS = auto()
    ADMIN = auto()

@dataclass
class UserToken:
    """Represents website app connections"""
    website: str
    access_token: str
    refresh_token: str
    token_expiry: datetime

    def __hash__(self):
        return hash(self.website)

@dataclass
class User:
    """Represents a user in the music system"""
    user_id: UUID
    username: str
    email: str
    hashed_password: str
    permissions: Set[Permission] = field(default_factory=set)
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    connections: Dict[str, UserToken] = field(default_factory=dict)
    is_active: bool = True

    def __hash__(self):
        return hash(self.user_id)

    def __eq__(self, other):
        if not isinstance(other, User):
            return NotImplemented
        return self.user_id == other.user_id

    def update_last_active(self) -> None:
        """Update the last active timestamp"""
        self.last_active = datetime.now()

    def add_connection(self, key: str, token: UserToken) -> None:
        """Add a new connection token"""
        self.connections[key] = token

    def remove_connection(self, key: str) -> None:
        """Remove a connection token"""
        self.connections.pop(key, None)

    def login(self, login_attempt_password: str) -> bool:
        """Login the user"""
        is_valid = bcrypt.checkpw(
            login_attempt_password.encode('utf-8'),
            self.hashed_password.encode('utf-8')
        )
        if is_valid:
            self.is_active = True
        return is_valid

    def logout(self) -> None:
        """Logout the user"""
        self.update_last_active()
        self.is_active = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert User instance to dictionary for serialization"""
        return {
            "user_id": str(self.user_id),
            "username": self.username,
            "email": self.email,
            "hashed_password": self.hashed_password,
            "permissions": [p.name for p in self.permissions],
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat(),
            "connections": {
                k: {
                    "website": v.website,
                    "access_token": v.access_token,
                    "refresh_token": v.refresh_token,
                    "token_expiry": v.token_expiry.isoformat()
                } for k, v in self.connections.items()
            },
            "is_active": self.is_active
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        """Create User instance from dictionary"""
        connections = {
            k: UserToken(
                website=v["website"],
                access_token=v["access_token"],
                refresh_token=v["refresh_token"],
                token_expiry=datetime.fromisoformat(v["token_expiry"])
            ) for k, v in data.get("connections", {}).items()
        }

        return cls(
            user_id=UUID(data["user_id"]),
            username=data["username"],
            email=data["email"],
            hashed_password=data["hashed_password"],
            permissions={Permission[p] for p in data.get("permissions", [])},
            created_at=datetime.fromisoformat(data["created_at"]),
            last_active=datetime.fromisoformat(data["last_active"]),
            connections=connections,
            is_active=data.get("is_active", True)
        )

@dataclass
class Artist:
    """Represents a music artist"""
    artist_id: str
    name: str
    genres: List[str] = field(default_factory=list)
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
    tracks: List[Track] = field(default_factory=list)
    album_type: str = "album"
    total_tracks: int = 0
    image_url: Optional[str] = None
    genres: List[str] = field(default_factory=list)

@dataclass
class PlaybackState:
    """Represents the current playback state"""
    is_playing: bool = False
    position_ms: int = 0
    volume_percent: int = 50
    repeat_mode: str = "off"
    shuffle_mode: bool = False

@dataclass
class QueueItem:
    """Represents an item in the playback queue"""
    track: Track
    requested_by: User
    requested_at: datetime = field(default_factory=datetime.now)
    votes: Set[UUID] = field(default_factory=set)
    position: int = 0
