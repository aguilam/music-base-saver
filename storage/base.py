from abc import ABC, abstractmethod
from pathlib import Path


class Storage(ABC):
    @classmethod
    @abstractmethod
    def TAG(cls) -> str:
        pass

    def __init__(self, config):
        self.config = config

    @abstractmethod
    def save_file(file: Path) -> str:
        pass

    @abstractmethod
    def delete_file(file: Path) -> bool:
        pass

    @abstractmethod
    def get_file(file: Path):
        pass

    @abstractmethod
    def get_all_tracks_paths() -> list[str]:
        pass

    @abstractmethod
    def check_storage() -> int:
        pass

    @abstractmethod
    def get_range_bytes(path: str, start: int, end: int) -> dict:
        pass
