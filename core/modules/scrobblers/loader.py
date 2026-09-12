from core.loader import ModuleEntry, import_modules, load_modules
from core.modules.scrobblers.base import Scrobbler
from core.schemas import ServiceStatus


def load_scrobblers(
    config: dict,
) -> tuple[list[ModuleEntry[Scrobbler]], list[ServiceStatus]]:
    return load_modules(config, import_modules(__file__, Scrobbler))
