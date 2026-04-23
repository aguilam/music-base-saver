from abc import ABC, abstractmethod
from core.schemas.schemas import Track, Album, Artist, Playlist


class Importer(ABC):

    @classmethod
    @abstractmethod
    def TAG(cls) -> str:
        pass

    def __init__(self, config):
        self.config = config

    @abstractmethod
    def get_favorited(self):
        pass

    @abstractmethod
    def get_tracks(self) -> list[Track]:
        pass

    @abstractmethod
    def get_albums(self) -> list[Album]:
        pass

    @abstractmethod
    def get_artists(self) -> list[Artist]:
        pass

    @abstractmethod
    def get_playlists(self) -> list[Playlist]:
        pass

    @abstractmethod
    def get_playlist(self) -> Playlist:
        pass

    @abstractmethod
    def get_track_download(self) -> str:
        pass

    @abstractmethod
    def get_lyrics(self):
        pass

    @abstractmethod
    def get_music_video(self):
        pass
