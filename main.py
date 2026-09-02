from interfaces.subsonic_api.main import SubsonicApi
from core.library_manager import LibraryManager
import asyncio


async def main():
    library_manager = LibraryManager()
    api = SubsonicApi(library_manager, {})
    await asyncio.gather(api.start())


if __name__ == "__main__":
    asyncio.run(main())
