from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, ClassVar

from structlog import BoundLogger

from core.schemas import HealthStatus, ServiceStatus

if TYPE_CHECKING:
    from core.modules.modules_manager import ModulesManager


class Service(ABC):
    TAG: ClassVar[str]

    @abstractmethod
    def health_check(self) -> HealthStatus:
        return HealthStatus(True)


class Module[T](ABC):
    ID: ClassVar[str]
    statuses: list[ServiceStatus]

    def __init__(
        self, modules: ModulesManager, config: dict[str, Any], logger: BoundLogger
    ):
        self.config = config
        self.logger = logger
        self.modules = modules
