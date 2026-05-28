import typer
from rich.console import Console, Group
from rich.live import Live
from rich.text import Text
from rich.spinner import Spinner
from core.library_manager import LibraryManager
import time
from core.schemas.schemas import Task, ImportTaskResult, ImportMetric

import_app = typer.Typer(help="Позволяет импортировать треки в базу")


@import_app.command("from")
def import_local(importer_tag: str):
    library_manager = LibraryManager()
    task_id = library_manager.import_library(importer_tag=importer_tag.upper())
    console = Console()
    entities = [
        "playlists",
        "tracks",
        "covers",
        "albums",
        "artists",
        "lyrics",
        "videos",
    ]
    with Live() as live:
        while True:
            import_result: Task[ImportTaskResult] | None = library_manager.get_task(
                task_id
            )
            console_text = _create_result_text(entities, import_result.result)
            live.update(
                Group(
                    Spinner("dots", text=import_result.status.capitalize()),
                    *console_text,
                ),
                refresh=True,
            )
            if import_result.status == "finished":
                console.print(f"Library importing from {importer_tag} finished")
                break
            if import_result.status == "error":
                console.print(
                    f"Error while importing from {importer_tag} - {import_result.error}"
                )
            time.sleep(0.5)


def _create_result_text(entities: list[str], import_result: ImportTaskResult):
    console_text = []
    for entity in entities:
        result_info: ImportMetric = getattr(import_result, entity)
        text = Text(f"{result_info.saved}/{result_info.searched} saved {entity}")
        console_text.append(text)
    return console_text
