from __future__ import annotations

import inspect
from importlib.abc import Loader
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import TYPE_CHECKING

from structlog import BoundLogger

from core.modules import Module

if TYPE_CHECKING:
    from core.modules.modules_manager import ModulesManager


def init_modules(
    modules: ModulesManager,
    logger: BoundLogger,
    config: dict,
    classes: dict[str, type[Module]],
) -> dict[str, Module]:
    modules_dict: dict[str, Module] = {}
    for id, class_type in classes.items():
        module_config = config.get(id, {})
        module_logger = logger.bind(module=id)
        modules_dict[id] = class_type(
            modules=modules, config=module_config, logger=module_logger
        )
    return modules_dict


def load_modules(current_path: str) -> dict[str, type[Module]]:
    path = Path.resolve(Path(current_path)).parent
    plugins_path = path.rglob("*.py")
    modules: dict[str, type[Module]] = {}
    for search in plugins_path:
        spec = spec_from_file_location(search.stem, str(search.resolve()))
        if spec is None or not isinstance(spec.loader, Loader):
            continue
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        for _, cls in inspect.getmembers(module, inspect.isclass):
            if (
                cls.__module__ == module.__name__
                and issubclass(cls, Module)
                and cls is not Module
            ):
                key = cls.ID
                modules[key] = cls
    return modules
