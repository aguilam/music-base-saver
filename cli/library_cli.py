from core.errors import BaseError
import typer
from core.library_manager import LibraryManager
from core.tasks.schemas import Task, SyncTaskResult, SyncMetric
from rich.console import Console
from rich.spinner import Spinner
from rich.table import Table
from rich.live import Live
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    MofNCompleteColumn,
)
from rich.console import Group
from rich.padding import Padding
from rich.text import Text
import time

library_app = typer.Typer(help="Действия с музыкальной библиотекой")
library_manager = LibraryManager()


@library_app.command("list")
def track_list():

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
    track = library_manager.delete_track(track_id)


@library_app.command("sync")
def sync():
    task_id = library_manager.sync()
    console = Console()
    progress_bar = Progress(
        SpinnerColumn(),
        TextColumn("{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
    )
    sync_progress_task = progress_bar.add_task("Syncing...", total=None)
    with Live(progress_bar) as live:
        while True:
            task = library_manager.get_sync_task(task_id)
            if isinstance(task, BaseError):
                Text(f"Error while syncing: {BaseError.detail}")
                return
            entities = ["tracks", "covers", "lyrics", "videos"]
            results: list[SyncMetric] = [
                getattr(task.result, entity) for entity in entities
            ]
            searched = sum([result.searched_new for result in results])
            processed = sum([result.processed for result in results])
            unbound_count = sum(
                [
                    len(getattr(task.result.unbound_files, entity))
                    for entity in ["covers", "lyrics", "videos"]
                ]
            )
            progress_bar.update(
                sync_progress_task,
                description=f"[bold yellow]{task.status.capitalize()}",
                total=searched,
                completed=processed,
            )
            texts = _create_sync_text(entities, task.result)
            live.update(
                Group(
                    progress_bar,
                    *texts,
                    Text(f"Undbound Files: {unbound_count}"),
                ),
                refresh=True,
            )
            if task.status == "finished":
                console.print("Scanning finished")
                break
            if task.status == "error":
                console.print(f"Error while library sync: {task.error}")
                break
            time.sleep(0.2)


def _create_sync_text(entities: list[str], import_result: SyncTaskResult):
    console_text = []
    for entity in entities:
        result_info: SyncMetric = getattr(import_result, entity)
        console_text.append(Text(entity.capitalize(), style="bold"))
        deleted_text = Text(
            f"New found: {result_info.searched_new}\nProcessed: {result_info.processed}\nAdded: {result_info.added}\nDeleted: {result_info.deleted}"
        )
        console_text.append(Padding(deleted_text, (0, 0, 1, 4)))
    return console_text


@library_app.command("stats")
def library_stats():
    console = Console()
    stats = library_manager.get_library_stats()
    stats_text = Group(
        Text(f"Total tracks: {stats.tracks_total}"),
        Text(f"Tracks with lyrics: {stats.tracks_with_lyrics}"),
        Text(f"Tracks with videos: {stats.tracks_with_videos}"),
        Text(""),
        Text(f"Total albums: {stats.albums_total}"),
        Text(f"Albums with cover: {stats.albums_with_cover}"),
        Text(""),
        Text(f"Total artists: {stats.artists_total}"),
        Text(f"Artists with cover {stats.artists_with_cover}"),
        Text(""),
        Text(f"Total lyrics: {stats.lyrics_total}"),
        Text(""),
        Text(f"Total videos: {stats.videos_total}"),
        Text(""),
        Text(f"Total genres: {stats.genres_total}"),
        Text(f"Artists with genres {stats.artists_with_genres}"),
        Text(f"Albums with genres {stats.albums_with_genres}"),
        Text(f"Tracks with genres {stats.tracks_with_genres}"),
        Text(""),
        Text(f"Total moods: {stats.moods_total}"),
        Text(f"Tracks with moods: {stats.tracks_with_moods}"),
    )
    console.print(stats_text)
