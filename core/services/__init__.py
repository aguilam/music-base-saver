from abc import ABC, abstractmethod
from core.schemas import HealthStatus
from typing import ClassVar


class Service(ABC):
    TAG: ClassVar[str]

    @abstractmethod
    def health_check(self) -> HealthStatus:
        return HealthStatus(True)
