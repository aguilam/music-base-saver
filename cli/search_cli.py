import typer
from core.library_manager import LibraryManager
from rich.console import Console
from rich.table import Table


search_app = typer.Typer(help="Поиск информации по источникам")


@search_app.command("global")
def search_track(query: str):
    library_manager = LibraryManager()
    searched = library_manager.global_search(query)
    table = Table(title="Треки")
    table.add_column("Title", style="magenta")
    table.add_column("Artist", style="magenta")
    table.add_column("Length", style="green")
    table.add_column("Source", style="green")
    for track in searched.tracks:
        artist = ", ".join([artist.name for artist in track.artists])
        table.add_row(
            track.title,
            artist,
            str(int(track.length / 1000)),
            track.external_id.split("-")[0],
        )
    console = Console()
    console.print(table)
