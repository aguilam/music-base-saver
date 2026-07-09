from typing import Generator
from abc import ABC, abstractmethod
from pathlib import Path
from core.base_service import Service


class Storage(Service, ABC):
    def __init__(self, config):
        self.config = config

    @abstractmethod
    def save_file(self, file_path: str, saving_path: str) -> str:
        pass

    @abstractmethod
    def delete_file(self, path: str) -> bool:
        pass

    @abstractmethod
    def get_file(self, path: str) -> str:
        pass

    @abstractmethod
    def get_all_files_paths(self) -> list[tuple[str, str]]:
        pass

    @abstractmethod
    def check_storage(self) -> int:
        pass

    @abstractmethod
    def get_file_metadata(self, path: str) -> dict:
        pass

    @abstractmethod
    def get_range_bytes(self, path: str, start: int, end: int) -> Generator[bytes]:
        pass
