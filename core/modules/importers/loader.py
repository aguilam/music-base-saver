from core.schemas import ServiceStatus
from core.modules.importers.base import Importer
from core.loader import load_modules, import_modules, ModuleEntry


def load_importers(
    config: dict,
) -> tuple[list[ModuleEntry[Importer]], list[ServiceStatus]]:
    return load_modules(
        config.get("importer", {}), import_modules("importer", Importer)
    )
