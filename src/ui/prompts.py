import os
import sys
import logging
from src.config.loader import load_config
from src.user.user_manager import UserManager
from src.session.session_manager import SessionManager
from src.config.settings import AppConfig

class SystemPrompt():
    def __init__(self, config: AppConfig, clearing: bool):
        self.config = config
        self.clearing = clearing

    def clear_screen(self) -> None:
        """Clears the terminal screen."""
        if self.clearing is False:
            return
        os.system('cls' if os.name == 'nt' else 'clear')

    def clear_screen_prompt(self) -> None:
        """Prompts for enter input and clears the terminal screen."""
        if self.clearing is False:
            return
        input("Press Enter to continue")
        self.clear_screen()

    def system_prompt_start(self) -> None:
        """Initiate the prompt"""
        user_manager = UserManager()
        session_manager = SessionManager(self.config, user_manager)

        user = None
        while not user:
            try:
                self.clear_screen()
                login_choice = input("1: Login\n2: Create Account\nChoice: ")
                self.clear_screen()
                if login_choice not in ["1", "2"]:
                    raise ValueError("Please choose either option 1 or 2")

                if login_choice == "1":
                    user = user_manager.user_login_prompt()

                if login_choice == "2":
                    user = user_manager.user_creation_prompt()

            except ValueError as e:
                print(f"Error: {e}")
                self.clear_screen_prompt()


        while True:
            try:
                self.clear_screen()
                session_choice = input("1: Create session\n2: Join session\n3: List sessions\nChoice: ")

                if session_choice not in ["1", "2", "3"]:
                    raise ValueError("Invalid choice. Please choose a valid option.")

                if session_choice == "1":
                    self.clear_screen()
                    session_name = input("Choose a name: ")
                    session = session_manager.create_session(session_name, user)
                    break

                if session_choice == "2":
                    pass

                if session_choice == "3":
                    pass

            except ValueError as e:
                print(f"Error: {e}")
                self.clear_screen_prompt()

        while True:
            try:
                self.clear_screen()
                session_choice = input("1: Request song\n2: List songs\n3: Vote\nChoice: ")

                if session_choice not in ["1", "2", "3", "4"]:
                    raise ValueError("Invalid choice. Please choose a valid option.")

                if session_choice == "1":
                    self.clear_screen()
                    song_query = input("Type song name: ")
                    self.clear_screen()
                    print("Searching...")
                    search_result = session_manager.music_provider.search_tracks(song_query, 5)
                    self.clear_screen()
                    for index, song in enumerate(search_result):
                        print(f"{index}: Title: {song.title}, Artist: {song.artist.name}, Album title: {song.album.title}")
                    song_choice = input("Choose a song: ")
                    if int(song_choice) > 5:
                        raise ValueError("Invalid choice. Please choose a valid option.")

                    session_manager.add_track_request(session.session_id, search_result[int(song_choice)], user)
                    self.clear_screen()

                if session_choice == "2":
                    self.clear_screen()
                    queue = session_manager.get_queue(session.session_id)
                    for song in queue:
                        print(f"Title: {song.track.title}\tArtist: {song.track.artist.name}\tRequested by: {song.requested_by.username}\tVotes: {len(song.votes)}")
                    self.clear_screen_prompt()

                if session_choice == "3":
                    pass

            except ValueError as e:
                print(f"Error: {e}")
                self.clear_screen_prompt()


def main():
    config = load_config("config.yaml")

    prompt = SystemPrompt(config, sys.argv[1] == "True")

    prompt.system_prompt_start()

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()
