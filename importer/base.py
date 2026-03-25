from abc import ABC, abstractmethod
from core.db.models import Track, Album, Artist
from pathlib import Path


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
    def get_albums(self):
        pass

    @abstractmethod
    def get_artists(self):
        pass

    @abstractmethod
    def get_playlists(self):
        pass

    @abstractmethod
    def get_playlist(self):
        pass

    @abstractmethod
    def get_track_download(self) -> str:
        pass

    @abstractmethod
    def get_lyrics(self):
        pass
