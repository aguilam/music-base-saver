from pathlib import Path

config_path = Path("config.toml")
if not config_path.exists():
    config_path.write_text("", encoding="utf-8")

from interfaces.subsonic_api.main import SubsonicApi
from core.library_manager import LibraryManager
from interfaces.music_saver.main import WebUi
import asyncio


async def main():
    library_manager = LibraryManager()

    api = SubsonicApi(library_manager, {})
    web_ui = WebUi(library_manager, {})
    await asyncio.gather(api.start(), web_ui.start())


if __name__ == "__main__":
    asyncio.run(main())
