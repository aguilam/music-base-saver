from abc import ABC, abstractmethod
from core.db.models import Track


class Scrobbler(ABC):

    @classmethod
    @abstractmethod
    def TAG(cls) -> str:
        pass

    @abstractmethod
    def post_playing_now(track: Track):
        pass

    @abstractmethod
    def submit_listen(track: Track, time: int | None):
        pass
