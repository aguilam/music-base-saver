import typer
from core.library_manager import LibraryManager
from core.schemas.schemas import Task, SyncTaskResult
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.console import Group
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
    task_id = library_manager.post_task()
    console = Console()
    added_text = Text("Added: 0")
    deleted_text = Text("Deleted: 0")
    with Live(Group(added_text, deleted_text), auto_refresh=False) as live:
        while True:
            task: Task[SyncTaskResult] | None = library_manager.get_task(task_id)
            added_text.plain = f"Added: {task.result.added}"
            deleted_text.plain = f"Deleted: {task.result.deleted}"
            live.refresh()
            if task.status == "finished":
                break
            time.sleep(0.2)
    console.print("Scanning finished")
