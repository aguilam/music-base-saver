import typer
from core.library_manager import LibraryManager
from rich.console import Console
from rich.table import Table
from rich.progress import Progress
import time
from typing import Annotated

download_app = typer.Typer(help="Загрузить новый трек")


@download_app.command("track")
def search_track(
    query: Annotated[
        str | None, typer.Option("--query", "-q", help="search by track name")
    ] = None,
    id: Annotated[
        str | None, typer.Option("--id", "-i", help="search by external api id")
    ] = None,
):
    if query is None and id is None:
        raise typer.BadParameter("Give --id or --query parametr")
    library_manager = LibraryManager()
    console = Console()
    console.print(f"Начат поиск и загрузка трека - {query}", style="green")
    track_id = library_manager.post_download(query=query, id=id)
    track = None
    with Progress() as progress_bar:
        download_task = progress_bar.add_task("[green]Скачка", total=100)
        while True:
            task = library_manager.get_download_task(track_id)
            progress_bar.update(download_task, completed=task["progress"])
            if task["status"] == "Finished":
                track = task.get("result")
                break
            time.sleep(0.3)
    console.print(
        f" \nЗагрузка с [bold green]{track["download_source"]}[/] завершена, трек сохранён в [bold blue]{track["storage"]}[/] по пути [yellow]{track["saved_path"]}[/]"
    )
    table = Table(title="Метаданные сохранённого трека")
    table.add_column("Title", style="magenta")
    table.add_column("Artist", style="cyan")
    table.add_column("Length", style="green")
    artist = ", ".join(track["artist"])
    table.add_row(track["title"], artist, str(int(track["length"])))
    console.print(table)
