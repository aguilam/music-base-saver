from abc import ABC, abstractmethod
from typing import Callable


class Downloader(ABC):
    @classmethod
    @abstractmethod
    def TAG(cls) -> str:
        pass

    def __init__(self, config):
        self.config = config

    @abstractmethod
    def search(query: str) -> list[dict]:
        pass

    @abstractmethod
    def check_progress() -> bool:
        pass

    @abstractmethod
    def download(track, progress_callback: Callable[[int], None]) -> str:
        pass
