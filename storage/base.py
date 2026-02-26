from abc import ABC, abstractmethod
from pathlib import Path
from core.schemas import Track


class Storage(ABC):
    @classmethod
    @abstractmethod
    def TAG(cls) -> str:
        pass

    def __init__(self, config):
        self.config = config

    @abstractmethod
    def save_track(file: Path) -> Path:
        pass

    @abstractmethod
    def delete_track(track_id: str) -> bool:
        pass

    @abstractmethod
    def check_storage() -> int:
        pass

    @abstractmethod
    def get_track(track_id: str):
        pass
