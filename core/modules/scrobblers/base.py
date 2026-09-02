from core.modules import Service
from abc import ABC, abstractmethod
from core.schemas import Track, Artist


class Scrobbler(Service, ABC):
    @abstractmethod
    def post_playing_now(self, track: Track, token: str):
        pass

    @abstractmethod
    def submit_listen(self, track: Track, token: str, time: int | None):
        pass

    @abstractmethod
    def get_tracks_recommendations(self, user_token: str, count: int) -> list[Track]:
        pass

    @abstractmethod
    def get_similiar_artists(self, artist: Artist) -> list[str]:
        pass
