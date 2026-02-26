from abc import ABC, abstractmethod


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
    def check_progress() -> bool:
        pass

    @abstractmethod
    def download():
        pass
