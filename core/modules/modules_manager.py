from __future__ import annotations

from typing import cast

from structlog import BoundLogger

from core.errors import BaseError, NotFoundError
from core.modules import Module
from core.modules.loader import init_modules, load_modules
from core.schemas import ServiceStatus


class ModulesManager:
    def __init__(self, logger: BoundLogger, modules_config: dict):
        self._modules = init_modules(
            self, logger, modules_config, load_modules(__file__)
        )

    def get[T: Module](self, module_class: type[T]) -> T | BaseError:
        module = self._modules.get(module_class.ID)
        if module is None:
            return NotFoundError(detail=f"Module {module_class.ID} not found")

        if not isinstance(module[0], module_class):
            return NotFoundError(detail=(f"Module {module_class.ID} has wrong type"))
        return cast(T, module[0])

    def get_module_statuses(self, id: str) -> list[ServiceStatus] | BaseError:
        module = self._modules.get(id)
        if module is None:
            return NotFoundError(detail=f"Module {id} not found")
        return module[1]
