from abc import ABC, abstractmethod
from pathlib import Path
from core.base_service import Service


class Storage(Service, ABC):

    def __init__(self, config):
        self.config = config

    @abstractmethod
    def save_file(self, file: Path) -> str:
        pass

    @abstractmethod
    def delete_file(self, file: Path) -> bool:
        pass

    @abstractmethod
    def get_file(self, file: Path) -> str:
        pass

    @abstractmethod
    def get_all_tracks_paths(self) -> list[tuple[str, str]]:
        pass

    @abstractmethod
    def check_storage(self) -> int:
        pass

    @abstractmethod
    def get_range_bytes(self, path: str, start: int, end: int) -> dict:
        pass
