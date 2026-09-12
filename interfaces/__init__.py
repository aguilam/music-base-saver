from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from core.library_manager import LibraryManager


class Interface(ABC):
    ID: ClassVar[str]

    def __init__(self, library_manager: "LibraryManager", config: dict):
        self.library_manager = library_manager
        self.config = config

    @abstractmethod
    async def start(self):
        pass
