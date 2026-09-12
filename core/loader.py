import inspect
from dataclasses import dataclass
from importlib.abc import Loader
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any

from core.schemas import HealthStatus, ServiceStatus


@dataclass(slots=True)
class ModuleEntry[T]:
    tag: str
    priority: int
    params: dict[str, Any]
    instance: T


# TODO: Rename to maybe plugin
def import_modules[T](current_path: str, BaseClass: type[T]) -> dict[str, type[T]]:
    path = Path.resolve(Path(current_path)).parent
    searchs_path = (path / "builtin").glob("*.py")
    plugins_path = (path / "external").glob("*.py")
    searched_modules = [*searchs_path, *plugins_path]
    modules: dict[str, type[T]] = {}
    for search in searched_modules:
        spec = spec_from_file_location(search.stem, str(search.resolve()))
        if spec is None or not isinstance(spec.loader, Loader):
            continue
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        for _, cls in inspect.getmembers(module, inspect.isclass):
            if (
                cls.__module__ == module.__name__
                and issubclass(cls, BaseClass)
                and cls is not BaseClass
            ):
                key = getattr(cls, "TAG", None) or getattr(cls, "NAME", None)
                if key is None:
                    continue
                modules[key] = cls
    return modules


def load_modules[T](
    config: dict, module_classes: dict[str, type[T]]
) -> tuple[list[ModuleEntry[T]], list[ServiceStatus]]:
    modules: list[ModuleEntry[T]] = []
    errors = []
    for module, settings in config.items():
        try:
            cls = module_classes[module]
            if cls and settings.get("enabled", True):
                params: dict = settings.get("params", {})
                modules.append(
                    ModuleEntry(
                        module, settings.get("priority", 0), params, cls(params)
                    )
                )
        except Exception as e:
            errors.append(
                ServiceStatus(
                    tag=module,
                    health=HealthStatus(ok=False, message=str(e)),
                )
            )
    modules.sort(key=lambda x: x.priority, reverse=True)
    return modules, errors
