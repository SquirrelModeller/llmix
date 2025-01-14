from typing import Literal, Optional
from pydantic import BaseModel, validator

# pylint: disable=no-self-argument,missing-function-docstring,missing-class-docstring

class OpenAISettings(BaseModel):
    api_key: Optional[str]

class LLMConfig(BaseModel):
    provider: Literal["openai"]
    openai: Optional[OpenAISettings] = None

    @validator('openai')
    def validate_openai_config(cls, v, values):
        if v is None:
            raise ValueError("Incorrect config for provider")
        return v

class SpotifySettings(BaseModel):
    client_id: Optional[str]
    client_secret: Optional[str]

class MusicConfig(BaseModel):
    provider: Literal["spotify"]
    spotify: Optional[SpotifySettings] = None

    @validator('spotify')
    def validate_spotify_config(cls, v, values):
        if v is None:
            raise ValueError("Incorrect config for provider")
        return v

class AppConfig(BaseModel):
    llm: LLMConfig
    music: MusicConfig

    class Config:
        extra = "forbid"
