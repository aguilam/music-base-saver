import asyncio
from pathlib import Path

import structlog
import tomllib

from core.library_manager import LibraryManager
from core.modules.modules_manager import ModulesManager
from loader import init_interfaces, load_interfaces


async def main():
    config_path = Path("config.toml")
    if not config_path.exists():
        config_path.write_text("", encoding="utf-8")
    config = tomllib.loads(config_path.read_text(encoding="utf-8"))
    logger = structlog.getLogger()
    manager = ModulesManager(logger, config.get("modules", {}))
    library_manager = LibraryManager(manager)
    interfaces = init_interfaces(
        library_manager, config.get("interfaces", {}), load_interfaces(__file__)
    )
    await asyncio.gather(*(interface.start() for interface in interfaces.values()))


if __name__ == "__main__":
    asyncio.run(main())
