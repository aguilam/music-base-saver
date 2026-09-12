from core.loader import ModuleEntry, import_modules, load_modules
from core.modules.downloaders.base import Downloader
from core.schemas import ServiceStatus


def load_downloaders(
    config: dict,
) -> tuple[list[ModuleEntry[Downloader]], list[ServiceStatus]]:
    return load_modules(
        config,
        import_modules(__file__, Downloader),
    )
