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
    def search(self, query: str) -> list[dict]:
        pass

    @abstractmethod
    def check_progress(self) -> bool:
        pass

    @abstractmethod
    def download(self, track, progress_callback: Callable[[int], None]) -> str:
        pass
