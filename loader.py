import inspect
from importlib.abc import Loader
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from core.library_manager import LibraryManager
from interfaces import Interface


def init_interfaces(
    library_manager: LibraryManager,
    config: dict,
    classes: dict[str, type[Interface]],
) -> dict[str, Interface]:
    interfaces_dict: dict[str, Interface] = {}
    for id, interface in classes.items():
        interface_config = config.get(id, {})
        if not interface_config.get("enabled", True):
            continue
        interfaces_dict[id] = interface(
            library_manager=library_manager, config=interface_config
        )
    return interfaces_dict


def load_interfaces(current_path: str) -> dict[str, type[Interface]]:
    path = Path.resolve(Path(current_path)).parent / "interfaces"
    plugins_path = path.rglob("*.py")
    modules: dict[str, type[Interface]] = {}
    for search in plugins_path:
        spec = spec_from_file_location(search.stem, str(search.resolve()))
        if spec is None or not isinstance(spec.loader, Loader):
            continue
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        for _, cls in inspect.getmembers(module, inspect.isclass):
            if (
                cls.__module__ == module.__name__
                and issubclass(cls, Interface)
                and cls is not Interface
            ):
                key = cls.ID
                modules[key] = cls
    return modules
