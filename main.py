from pathlib import Path

import structlog

from core.modules.modules_manager import ModulesManager
from loader import init_interfaces, load_interfaces

config_path = Path("config.toml")
if not config_path.exists():
    config_path.write_text("", encoding="utf-8")

import asyncio

from core.library_manager import LibraryManager


async def main():
    logger = structlog.getLogger()
    manager = ModulesManager(logger, {})
    library_manager = LibraryManager(manager)
    interfaces = init_interfaces(library_manager, {}, load_interfaces(__file__))
    await asyncio.gather(*(interface.start() for interface in interfaces.values()))


if __name__ == "__main__":
    asyncio.run(main())
