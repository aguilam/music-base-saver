from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import ClassVar, Any


class Tool(ABC):
    NAME: ClassVar[str]

    @abstractmethod
    def METHODS(self) -> dict[str, Callable[..., Any]]:
        pass
