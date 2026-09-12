from pathlib import Path

import structlog

from core.modules.modules_manager import ModulesManager

config_path = Path("config.toml")
if not config_path.exists():
    config_path.write_text("", encoding="utf-8")

import asyncio

from core.library_manager import LibraryManager
from interfaces.music_saver.main import WebUi
from interfaces.subsonic_api.main import SubsonicApi


async def main():
    logger = structlog.getLogger()
    manager = ModulesManager(logger, {})
    library_manager = LibraryManager(manager)
    api = SubsonicApi(library_manager, {})
    web_ui = WebUi(library_manager, {})
    await asyncio.gather(api.start(), web_ui.start())


if __name__ == "__main__":
    asyncio.run(main())
