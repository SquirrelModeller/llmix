import json
import logging
from openai import OpenAI
from src.llm.load_prompt import load_prompt
from src.llm.llm_bridge import MusicLLMBridge
from src.user.user_manager import UserManager

logger = logging.getLogger(__name__)

class OpenAIMusicAssistant:
    def __init__(self, api_key: str, model: str, music_bridge: MusicLLMBridge, user_manager: UserManager):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.music_bridge = music_bridge
        self.user_manager = user_manager

    def process_message(self, message: str, username: str) -> str:
        """Process a user message and execute any necessary music functions"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": load_prompt("./ai_prompts/playlist/playlist_manager.txt")},
                {"role": "user", "content": message}
            ],
            functions=self.music_bridge.function_schemas,
            function_call="auto"
        )

        if response.choices[0].message.function_call:
            function_call = response.choices[0].message.function_call
            try:
                function_arguments = json.loads(function_call.arguments)

                result = self.music_bridge.execute_function(
                    function_call.name,
                    self.user_manager,
                    username=username,
                    **function_arguments
                )

                if function_call.name == "search_tracks":
                    formatted_result = [
                        self.music_bridge.format_track_response(track)
                        for track in result
                    ]
                elif function_call.name == "get_track":
                    formatted_result = self.music_bridge.format_track_response(result)
                elif function_call.name == "get_artist":
                    formatted_result = self.music_bridge.format_artist_response(result)
                else:
                    formatted_result = result

                final_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": load_prompt('./ai_prompts/playlist/playlist_manager.txt')},
                        {"role": "user", "content": message},
                        {"role": "assistant", "content": None, "function_call": function_call},
                        {"role": "function", "name": function_call.name, "content": str(formatted_result)}
                    ]
                )
                logger.debug("AI Response: %s", final_response.choices[0].message.content)
                return final_response.choices[0].message.content
            except Exception as e:
                return f"Error executing music function: {str(e)}"

        return response.choices[0].message.content


def main():
    from src.config.loader import load_config
    from src.music.factory import MusicFactory

    config = load_config("config.yaml")
    music_provider = MusicFactory.create(config.music)
    user_manager = UserManager()

    bridge = MusicLLMBridge(music_provider)
    assistant = OpenAIMusicAssistant(
        api_key=config.llm.openai.api_key,
        model="gpt-3.5-turbo",
        music_bridge=bridge,
        user_manager=user_manager
    )

    message = "Create me an empty playlist called BANGERS. The username is example"
    username = "example"

    response = assistant.process_message(message, username)
    print(response)

if __name__ == "__main__":
    main()
