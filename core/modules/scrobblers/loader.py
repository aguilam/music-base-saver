from core.schemas import ServiceStatus
from core.modules.scrobblers.base import Scrobbler
from core.loader import load_modules, import_modules, ModuleEntry


def load_scrobblers(
    config: dict,
) -> tuple[list[ModuleEntry[Scrobbler]], list[ServiceStatus]]:
    return load_modules(
        config.get("scrobbler", {}), import_modules("scrobbler", Scrobbler)
    )
