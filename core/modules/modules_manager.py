from __future__ import annotations

from typing import cast

from structlog import BoundLogger

from core.errors import BaseError, NotFoundError
from core.modules import Module
from core.modules.loader import init_modules, load_modules


class ModulesManager:
    def __init__(self, logger: BoundLogger, modules_config: dict):
        self._modules: dict[str, Module] = init_modules(
            self, logger, modules_config, load_modules(__file__)
        )

    def get[T: Module](self, module_class: type[T]) -> T | BaseError:
        module = self._modules.get(module_class.ID)

        if module is None:
            return NotFoundError(detail=f"Module {module_class.ID} not found")

        if not isinstance(module, module_class):
            return NotFoundError(detail=(f"Module {module_class.ID} has wrong type"))
        return cast(T, module)
