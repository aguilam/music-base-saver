from abc import ABC, abstractmethod
from core.schemas.schemas import HealthStatus


class Service(ABC):

    @classmethod
    @abstractmethod
    def TAG(cls) -> str:
        pass

    @abstractmethod
    def health_check(self) -> HealthStatus:
        return HealthStatus(True)
