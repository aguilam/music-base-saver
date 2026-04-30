from abc import ABC, abstractmethod
from core.schemas.schemas import Track, Album, Artist
from core.base_service import Service


class Search(Service, ABC):

    def __init__(self, config):
        self.config = config

    @abstractmethod
    def search_tracks(self, query: str) -> list[Track]:
        pass

    @abstractmethod
    def search_albums(self, query: str) -> list[Album]:
        pass

    @abstractmethod
    def search_artists(self, query: str) -> list[Artist]:
        pass

    @abstractmethod
    def get_track(self, id: str) -> Track:
        pass

    @abstractmethod
    def get_album(self, id: str) -> Album:
        pass

    @abstractmethod
    def get_artist(self, id: str) -> Artist:
        pass
