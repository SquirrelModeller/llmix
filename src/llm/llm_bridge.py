from typing import List, Dict, Any
from src.music.components import Track, Artist
from src.music.base_music import BaseMusic

class MusicLLMBridge:
    """Bridge class that exposes music provider functions to LLM"""

    def __init__(self, music_provider: BaseMusic):
        self.music = music_provider
        self.function_schemas = self._generate_function_schemas()

    def _generate_function_schemas(self) -> List[Dict[str, Any]]:
        """Generate OpenAI function schemas for music provider methods"""
        return [
            {
                "name": "search_tracks",
                "description": "Search for music tracks based on a query",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for tracks"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return",
                            "default": 20
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_track",
                "description": "Get detailed information about a specific track",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "track_id": {
                            "type": "string",
                            "description": "ID of the track to retrieve"
                        }
                    },
                    "required": ["track_id"]
                }
            },
            {
                "name": "get_artist",
                "description": "Get detailed information about a specific artist",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "artist_id": {
                            "type": "string",
                            "description": "ID of the artist to retrieve"
                        }
                    },
                    "required": ["artist_id"]
                }
            },
            {
                "name": "get_user_playlists",
                "description": "Get all playlists for a given user",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "username": {
                            "type": "string",
                            "description": "Username of the user whose playlists to retrieve"
                        }
                    },
                    "required": ["username"]
                }
            },
            # {
            #     "name": "create_playlist",
            #     "description": "Create a new playlist for a user",
            #     "parameters": {
            #         "type": "object",
            #         "properties": {
            #             "name": {
            #                 "type": "string",
            #                 "description": "Name of the playlist"
            #             },
            #             "description": {
            #                 "type": "string",
            #                 "description": "Description of the playlist"
            #             },
            #             "public": {
            #                 "type": "boolean",
            #                 "description": "Whether the playlist should be public",
            #                 "default": True
            #             }
            #         },
            #         "required": ["name"]
            #     }
            # },
            {
                "name": "add_tracks_to_playlist",
                "description": "Add tracks to a user's playlist",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "playlist_id": {
                            "type": "string",
                            "description": "ID of the playlist to add tracks to"
                        },
                        "track_uris": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "List of track URIs to add"
                        }
                    },
                    "required": ["playlist_id", "track_uris"]
                }
            },
            {
                "name": "set_playlist_track_order",
                "description": "Reorders tracks in a playlist to match the specified sequence, inserting them at the specified track.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "playlist_id": {
                            "type": "string",
                            "description": "ID of the playlist to modify"
                        },
                        "track_sequence": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "List of track IDs in the desired order",
                        },
                        "insert_at_track": {
                            "type": "string",
                            "description": "Track ID where the sequence should be inserted"
                        }
                    },
                    "required": ["playlist_id", "track_sequence", "insert_at_track"]
                }
            }
        ]

    def execute_function(self, function_name: str, user_manager, **kwargs) -> Any:
        """Execute a music provider function with given parameters"""
        if function_name not in [schema["name"] for schema in self.function_schemas]:
            raise ValueError(f"Unknown function: {function_name}")

        if "username" in kwargs:
            username = kwargs.pop("username")
            user = user_manager.get_user_by_username(username)
            if not user:
                raise ValueError(f"User not found: {username}")
            kwargs["user"] = user

        return getattr(self.music, function_name)(**kwargs)

    def format_track_response(self, track: Track) -> Dict[str, Any]:
        """Format track information for LLM consumption"""
        return {
            "id": track.track_id,
            "name": track.title,
            "artists": track.artist,
            "album": track.album.title if track.album else None,
            "duration_ms": track.duration_ms
        }

    def format_artist_response(self, artist: Artist) -> Dict[str, Any]:
        """Format artist information for LLM consumption"""
        return {
            "id": artist.artist_id,
            "name": artist.name,
            "genres": artist.genres,
            "popularity": artist.popularity
        }

def main():
    from src.config.loader import load_config
    from src.music.factory import MusicFactory
    from src.user.user_manager import UserManager

    config = load_config("config.yaml")
    music_provider = MusicFactory.create(config.music)
    bridge = MusicLLMBridge(music_provider)
    user_manager = UserManager()

    # results = bridge.execute_function(
    #     "search_tracks",
    #     user_manager,
    #     query="YMCA",
    #     limit=5
    # )

    results = bridge.execute_function(
        "create_playlist",
        user_manager,
        username="example",
        name="testing",
        description="testing creation of playlist",
        public=True
    )

    # formatted_results = [bridge.format_track_response(track) for track in results]
    # print(formatted_results)

if __name__ == "__main__":
    main()
