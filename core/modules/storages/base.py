from core.modules.storages.schemas import FileMetadata
from core.modules import Service
from collections.abc import Iterator
from abc import ABC, abstractmethod


class Storage(Service, ABC):
    def __init__(self, config):
        self.config = config
        self.id = config["id"]
        self.name = config["name"]

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
    def get_file_metadata(self, path: str) -> FileMetadata:
        pass

    @abstractmethod
    def get_range_bytes(self, path: str, start: int, end: int) -> Iterator[bytes]:
        pass
