from importlib.abc import Loader
from collections import defaultdict
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
from storage.base import Storage
import inspect
from dataclasses import dataclass
from core.schemas.schemas import ServiceStatus, HealthStatus
from typing import TypeVar, Generic, Any, Callable
from tool.base import Tool, ToolFunction
from core.base_service import Service
from tool.events import Event

T = TypeVar("T")


@dataclass(slots=True)
class ModuleEntry(Generic[T]):
    tag: str
    priority: int
    params: dict[str, Any]
    instance: T


@dataclass(slots=True)
class StorageEntry(ModuleEntry[Storage]):
    id: str
    name: str


def import_modules(module_folder: str, BaseClass: type[T]) -> dict[str, type[T]]:
    path = Path.resolve(Path(__file__))
    searchs_path = (path.parents[1] / module_folder).glob("*.py")
    plugins_path = (path.parents[1] / "plugins" / module_folder).glob("*.py")
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


def load_modules(
    config: dict, module_classes: dict[str, type[T]]
) -> tuple[list[ModuleEntry[T]], list[ServiceStatus]]:
    modules: list[ModuleEntry[T]] = []
    errors = []
    for module, settings in config.items():
        try:
            cls = module_classes[module]
            if cls and settings.get("enabled", True):
                params = settings.get("params", {})
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


def load_storages(
    config: dict, storage_classes: dict[str, Any]
) -> tuple[list[StorageEntry], list[ServiceStatus]]:
    storages: dict = config.get("storage", {})
    active_storages: list[StorageEntry] = []
    errors = []
    for storage in storages:
        try:
            if storage.get("enabled", True):
                storage_tag = storage["tag"]
                instance_params = storage["params"]
                instance_params["id"] = storage["id"]
                instance_params["name"] = storage["name"]
                selected_storage = storage_classes[storage_tag]
                active_storages.append(
                    StorageEntry(
                        id=storage["id"],
                        name=storage["name"],
                        tag=storage_tag,
                        priority=storage["priority"],
                        params=storage["params"],
                        instance=selected_storage(instance_params),
                    )
                )
        except Exception as e:
            errors.append(
                ServiceStatus(
                    tag=storage.get("id", "Undefined"),
                    health=HealthStatus(ok=False, message=str(e)),
                )
            )
    active_storages.sort(key=lambda x: x.priority, reverse=True)
    return active_storages, errors


def load_tools(modules: dict[str, type[Tool]]) -> dict[Event, list[ToolFunction]]:
    tools: defaultdict[Event, list[ToolFunction]] = defaultdict(list)
    for module in modules.values():
        for _, method in inspect.getmembers(module, inspect.isfunction):
            if hasattr(method, "__event_name__"):
                tools[method.__event_name__].append(method)
    return dict(tools)
