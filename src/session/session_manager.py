from typing import List, Set, Dict, Optional, Any
from datetime import datetime
from uuid import UUID, uuid4
from dataclasses import dataclass, field
import logging
from src.music.components import User, Track, QueueItem, PlaybackState
from src.llm.providers.musicassistant import OpenAIMusicAssistant
from src.llm.llm_bridge import MusicLLMBridge
from src.music.factory import MusicFactory
from src.config.settings import AppConfig
from src.user.user_manager import UserManager

logger = logging.getLogger(__name__)

@dataclass
class Session:
    """Represents a music listening session"""
    session_id: UUID
    name: str
    initiator: User
    invited_users: Set[User]
    queue: List[QueueItem]
    playback_state: PlaybackState
    playlist: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)
    theme_keywords: List[str] = field(default_factory=list)


    def add_user(self, user: User) -> None:
        """Add a user to the session"""
        self.invited_users.add(user)

    def remove_user(self, user: User) -> None:
        """Remove a user from the session"""
        if user in self.invited_users:
            self.invited_users.remove(user)

    def vote_track(self, user_id: UUID, queue_position: int, upvote: bool = True) -> bool:
        """Vote on a track in the queue"""
        if 0 <= queue_position < len(self.queue):
            queue_item = self.queue[queue_position]
            if upvote:
                queue_item.votes.add(user_id)
            else:
                queue_item.votes.discard(user_id)
            return True
        return False

class SessionManager:
    """Manages music listening sessions"""
    def __init__(self, config: AppConfig, user_manager: UserManager):
        self.sessions: Dict[UUID, Session] = {}
        self.config = config
        self.user_manager = user_manager
        self._setup()

    def _setup(self):
        self.music_provider = MusicFactory.create(self.config.music)
        self.music_bridge = MusicLLMBridge(self.music_provider)

        self.assistant = OpenAIMusicAssistant(
            api_key=self.config.llm.openai.api_key,
            model="gpt-3.5-turbo",
            music_bridge=self.music_bridge,
            user_manager=self.user_manager
        )

    def create_session(self, name: str, initiator: User) -> Session:
        """Create a new music session"""
        session_id = uuid4()

        playlist, tracks = self.set_playlist(initiator, name)

        session = Session(
            session_id=session_id,
            name=name,
            initiator=initiator,
            invited_users=set(),
            queue=[],
            playback_state=PlaybackState(),
            playlist=playlist
        )
        for track in tracks:
            queue_item = QueueItem(
                    track=track,
                    requested_by=initiator,
                    position=len(session.queue)
                )
            queue_item.votes.add(initiator.user_id)
            session.queue.append(
                queue_item
            )

        self.sessions[session_id] = session
        return session

    def get_session(self, session_id: UUID) -> Optional[Session]:
        """Get a session by ID"""
        return self.sessions.get(session_id)

    def add_track_request(self, session_id: UUID, track: Track, requested_by: User) -> bool:
        """Add a track request to the session queue"""
        session = self.get_session(session_id)
        if not session:
            return False

        queue_item = QueueItem(
            track=track,
            requested_by=requested_by,
            position=len(session.queue)
        )

        queue_item.votes.add(requested_by.user_id)

        queue_context = self._get_queue_context(session)

        self._evaluate_track_placement(queue_context, track, session, requested_by)

        session.queue.append(queue_item)


    def set_playlist(self, user: User, target_playlist: str) -> Dict:
        """Initiate a playlist"""
        result = self.music_provider.get_user_playlists(user)
        playlist_target = None
        tracks = []
        for playlist in result:
            if playlist["name"] == target_playlist:
                songs = self.music_provider.get_user_playlist(user, playlist["id"])
                for i in songs["tracks"]["items"]:
                    tracks.append(self.music_provider._create_track(i["track"]))

                playlist_target = playlist


        if playlist_target:
            return (playlist_target, tracks)

        result = self.music_provider.create_playlist(user, target_playlist, "Session")

        return (result, tracks)

    def _get_queue_context(self, session: Session) -> Dict:
        """Get current queue context for LLM evaluation"""
        return {
            "current_queue": [
                {
                    "track": {
                        "title": item.track.title,
                        "artist": item.track.artist.name,
                        "genres": item.track.artist.genres,
                        "popularity": item.track.popularity
                    },
                    "votes": len(item.votes)
                } for item in session.queue
            ],
            "theme_keywords": session.theme_keywords
        }

    def _evaluate_track_placement(self, queue_context: Dict, new_track: Track, session: Session, user: User):
        """Ask LLM to evaluate where a new track should be placed in the queue"""

        prompt = f"""
        Playlist id: {session.playlist["id"]}
        User ID who owns the playlist: {user.connections['spotify'].info['id']}

        Current Queue: {queue_context}
        
        New Track:
        - Title: {new_track.title}
        - Track ID: {new_track.track_id}
        - Tack URI: {new_track.uri}
        - Artist: {new_track.artist.name}
        - Genres: {new_track.artist.genres}
        - Popularity: {new_track.popularity}
        """

        response = self.assistant.process_message(prompt, user.username)

    def _update_playlist(self, user: User, session: Session) -> None:
        """Updates the session playlist to the spotify"""

        self.music_provider.get_user_playlist(user, session.playlist["id"])

    def _update_queue_positions(self, session: Session) -> None:
        """Update position values for all items in queue"""
        for i, item in enumerate(session.queue):
            item.position = i

    def remove_track(self, session_id: UUID, position: int) -> bool:
        """Remove a track from the session queue"""
        session = self.get_session(session_id)
        if not session or position >= len(session.queue):
            return False

        session.queue.pop(position)
        self._update_queue_positions(session)
        return True

    def get_queue(self, session_id: UUID) -> List[QueueItem]:
        """Get the current queue for a session"""
        session = self.get_session(session_id)
        return session.queue if session else []
