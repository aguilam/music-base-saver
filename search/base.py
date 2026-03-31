from abc import ABC, abstractmethod


class Search(ABC):
    @classmethod
    @abstractmethod
    def TAG(cls) -> str:
        pass

    def __init__(self, config):
        self.config = config

    @abstractmethod
    def search_tracks(self, query: str) -> list[dict]:
        pass

    @abstractmethod
    def search_albums(self, query: str) -> list[dict]:
        pass

    @abstractmethod
    def search_artists(self, query: str) -> list[dict]:
        pass

    @abstractmethod
    def get_track(self, id: str) -> list[dict]:
        pass

    @abstractmethod
    def get_album(self, id: str) -> list[dict]:
        pass

    @abstractmethod
    def get_artist(self, id: str) -> list[dict]:
        pass
