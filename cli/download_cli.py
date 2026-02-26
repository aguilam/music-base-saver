import typer
from core.library_manager import LibraryManager
from rich.console import Console
from rich.table import Table
from rich.progress import Progress


download_app = typer.Typer(help="Загрузить новый трек")


@download_app.command("track")
def search_track(query: str):
    library_manager = LibraryManager()
    console = Console()
    console.print(f"Начат поиск и загрузка трека - {query}", style="green")
    progress = Progress()
    progress.start()
    download_task = progress.add_task("[green]Скачка", total=100)
    track = library_manager.download(
        query,
        lambda actual_progress: progress.update(
            download_task, completed=actual_progress
        ),
    )
    console.print(
        f" \nЗагрузка с [bold green]{track["download_source"]}[/] завершена, трек сохранён в [bold blue]{track["storage"]}[/] по пути [yellow]{track["saved_path"]}[/]"
    )
    table = Table(title="Метаданные сохранённого трека")
    table.add_column("Title", style="magenta")
    table.add_column("Artist", style="cyan")
    table.add_column("Length", style="green")
    artist = ", ".join(track["artist"])
    table.add_row(track["title"], artist, str(int(track["length"] / 1000)))
    console.print(table)
