import typer
from core.library_manager import LibraryManager
from rich.console import Console
from rich.table import Table


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
    library_manager.sync()
