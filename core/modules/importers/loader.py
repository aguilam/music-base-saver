from core.loader import ModuleEntry, import_modules, load_modules
from core.modules.importers.base import Importer
from core.schemas import ServiceStatus


def load_importers(
    config: dict,
) -> tuple[list[ModuleEntry[Importer]], list[ServiceStatus]]:
    return load_modules(config, import_modules(__file__, Importer))
