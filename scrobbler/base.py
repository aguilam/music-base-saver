from abc import ABC, abstractmethod
from core.schemas.schemas import Track


class Scrobbler(ABC):

    @classmethod
    @abstractmethod
    def TAG(cls) -> str:
        pass

    @abstractmethod
    def post_playing_now(self, track: Track, token: str):
        pass

    @abstractmethod
    def submit_listen(self, track: Track, token: str, time: int | None):
        pass
