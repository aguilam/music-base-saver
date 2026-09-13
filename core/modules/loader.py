from __future__ import annotations

import inspect
from importlib import import_module
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
    source = Path(current_path).resolve()

    root = source.parent if source.is_file() else source
    package_name = "core.modules"

    modules: dict[str, type[Module]] = {}

    for file in root.rglob("*.py"):
        if file.name == "__init__.py":
            continue

        relative = file.relative_to(root).with_suffix("")

        module_name = ".".join(
            (
                package_name,
                *relative.parts,
            )
        )

        loaded_module = import_module(module_name)
        for _, cls in inspect.getmembers(loaded_module, inspect.isclass):
            if (
                cls.__module__ == loaded_module.__name__
                and issubclass(cls, Module)
                and cls is not Module
            ):
                key = cls.ID
                modules[key] = cls
    return modules
