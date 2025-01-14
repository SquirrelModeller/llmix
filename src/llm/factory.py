import os
from src.config.settings import LLMConfig
from src.llm.providers.openai_provider import OpenAIProvider

class LLMFactory:
    @staticmethod
    def create(config: LLMConfig):
        if config.provider == "openai":
            api_key = os.environ.get("OPENAI_API_KEY")
            if api_key:
                config.openai.api_key = api_key

            return OpenAIProvider(config.openai)
