from core.schemas import ServiceStatus
from core.modules.downloaders.base import Downloader
from core.loader import load_modules, import_modules, ModuleEntry


def load_downloaders(
    config: dict,
) -> tuple[list[ModuleEntry[Downloader]], list[ServiceStatus]]:
    return load_modules(
        config.get("downloader", {}),
        import_modules("downloader", Downloader),
    )
