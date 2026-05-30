import typer
from core.library_manager import LibraryManager
from core.schemas.schemas import Task, SyncTaskResult, SyncMetric
from rich.console import Console
from rich.spinner import Spinner
from rich.table import Table
from rich.live import Live
from rich.console import Group
from rich.padding import Padding
from rich.text import Text
import time

library_app = typer.Typer(help="Действия с музыкальной библиотекой")


@library_app.command("list")
def track_list():
    library_manager = LibraryManager()

    tracks = library_manager.get_all_tracks()
    table = Table(title="Music Library")
    table.add_column("Id", justify="center", style="cyan", no_wrap=True)
    table.add_column("Title", style="magenta")
    table.add_column("Artist", justify="center", style="green")
    table.add_column("Length", justify="center", style="green")
    table.add_column("Link Provider", justify="center", style="green")
    for track in tracks:
        artist_str = ", ".join(track.artist)
        providers = ", ".join([link.link_provider for link in track.links])
        table.add_row(
            str(track.id), track.title, artist_str, str(track.length), providers
        )
    console = Console()
    console.print(table)


@library_app.command("del")
def delete_track(track_id: int):
    library_manager = LibraryManager()
    track = library_manager.delete_track(track_id)


@library_app.command("sync")
def sync():
    library_manager = LibraryManager()
    task_id = library_manager.sync()
    console = Console()
    with Live() as live:
        while True:
            task: Task[SyncTaskResult] | None = library_manager.get_task(task_id)
            texts = _create_sync_text(
                ["tracks", "covers", "lyrics", "videos"], task.result
            )
            live.update(
                Group(
                    Spinner("dots", text=task.status.capitalize()),
                    *texts,
                ),
                refresh=True,
            )
            if task.status == "finished":
                console.print("Scanning finished")
                break
            time.sleep(0.2)


def _create_sync_text(entities: list[str], import_result: SyncTaskResult):
    console_text = []
    for entity in entities:
        result_info: SyncMetric = getattr(import_result, entity)
        console_text.append(Text(entity.capitalize(), style="bold"))
        metrics_text = Text(
            f"Added: {result_info.added}\nDeleted: {result_info.deleted}"
        )
        console_text.append(Padding(metrics_text, (0, 0, 1, 4)))
    return console_text
