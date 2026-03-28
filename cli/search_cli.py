import typer
from core.library_manager import LibraryManager
from core.schemas import QueryType
from rich.console import Console
from rich.table import Table


search_app = typer.Typer(help="Поиск информации по источникам")


@search_app.command("track")
def search_track(query: str):
    library_manager = LibraryManager()
    tracks = library_manager.global_search(query, QueryType.TRACK)
    table = Table(title="Треки")
    table.add_column("Title", style="magenta")
    table.add_column("Artist", style="magenta")
    table.add_column("Length", style="green")
    table.add_column("Source", style="green")
    for track in tracks:
        artist = ", ".join(track["artist"])
        table.add_row(
            track["title"], artist, str(int(track["length"] / 1000)), track["source"]
        )
    console = Console()
    console.print(table)
