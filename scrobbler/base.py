from abc import ABC, abstractmethod
from core.schemas.schemas import Track, Artist
from core.base_service import Service


class Scrobbler(Service, ABC):

    @abstractmethod
    def post_playing_now(self, track: Track, token: str):
        pass

    @abstractmethod
    def submit_listen(self, track: Track, token: str, time: int | None):
        pass

    @abstractmethod
    def get_similiar_artists(self, artist: Artist) -> list[str]:
        pass
