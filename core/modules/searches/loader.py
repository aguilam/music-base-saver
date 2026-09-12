from core.loader import ModuleEntry, import_modules, load_modules
from core.modules.searches.base import Search
from core.schemas import ServiceStatus


def import_searches(
    config: dict,
) -> tuple[list[ModuleEntry[Search]], list[ServiceStatus]]:
    return load_modules(config, import_modules(__file__, Search))
