from core.schemas import ServiceStatus
from core.modules.searches.base import Search
from core.loader import load_modules, import_modules, ModuleEntry


def import_searches(
    config: dict,
) -> tuple[list[ModuleEntry[Search]], list[ServiceStatus]]:
    return load_modules(config.get("search", {}), import_modules("search", Search))
