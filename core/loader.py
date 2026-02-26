from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
import inspect


def import_modules(module_folder: str, BaseClass):
    path = Path.resolve(Path(__file__))
    searchs_path = (path.parents[1] / module_folder).glob("*.py")
    plugins_path = (path.parents[1] / "plugins" / module_folder).glob("*.py")
    searched_modules = [*searchs_path, *plugins_path]
    modules: dict[str, type] = {}
    for search in searched_modules:
        spec = spec_from_file_location(search.stem, str(search.resolve()))
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        for _, cls in inspect.getmembers(module, inspect.isclass):
            if (
                cls.__module__ == module.__name__
                and issubclass(cls, BaseClass)
                and cls is not BaseClass
            ):
                modules[getattr(cls, "TAG", None)] = cls
    return modules


def load_modules(config: dict, module_classes: dict):
    modules = []
    for module, settings in config.items():
        cls = module_classes[module]
        if cls and settings.get("enabled", True):
            modules.append(
                {
                    "tag": module,
                    "priority": settings.get("priority", 0),
                    "params": settings.get("params", {}),
                    "class": cls,
                }
            )
    modules.sort(key=lambda x: x["priority"], reverse=True)
    return modules


def load_storages(config: dict, storage_classes: dict):
    storages = config["storage"]
    active_storages = []
    for storage in storages:
        if storage["enabled"] == True:
            storage_tag = storage["tag"]
            selected_storage = storage_classes[storage_tag]
            active_storages.append(
                {
                    "id": storage["id"],
                    "name": storage["name"],
                    "tag": storage_tag,
                    "priority": storage["priority"],
                    "params": storage["params"],
                    "class": selected_storage,
                }
            )
    active_storages.sort(key=lambda x: x["priority"], reverse=True)
    return active_storages
