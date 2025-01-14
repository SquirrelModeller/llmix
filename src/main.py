from src.config.loader import load_config
from src.llm.factory import LLMFactory
from src.music.factory import MusicFactory

def main():
    config = load_config("config.yaml")

    # llm = LLMFactory.create(config.llm)

    music = MusicFactory.create(config.music)
    search = music.search_tracks("YMCA", 20)

    print(search)
    track = music.get_track(search[0].track_id)


if __name__ == "__main__":
    main()