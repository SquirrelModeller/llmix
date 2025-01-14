import logging
from openai import OpenAI
from src.llm.base_llm import BaseLLM
from src.config.settings import OpenAISettings

logger = logging.getLogger(__name__)

class OpenAIProvider(BaseLLM):
    def __init__(self, settings: OpenAISettings):
        super().__init__()
        self.settings = settings
        self.client = OpenAI(api_key=settings.api_key)

    def generate_response(self, input_text) -> str:

        try:
            response = self.client.chat.completions.create(
                messages=input_text,
                model="gpt-3.5-turbo",
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error("OpenAI API error: %s", e)
