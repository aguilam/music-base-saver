import typer
from core.library_manager import LibraryManager
from rich.table import Table
from rich.console import Console
from rich.text import Text
from core.schemas.schemas import ServiceStatus

library_manager = LibraryManager()

core_app = typer.Typer(help="Core utils")


@core_app.command("status")
def check_status():
    console = Console()
    statuses = library_manager.check_status()
    _print_statuses_table(console, "Search engines", statuses.search)
    _print_statuses_table(console, "Downloaders", statuses.downloaders)
    _print_statuses_table(console, "Scrobblers", statuses.scrobblers)
    _print_statuses_table(console, "Storages", statuses.storages)
    _print_statuses_table(console, "Importers", statuses.importers)


def _print_statuses_table(console: Console, title: str, statuses: list[ServiceStatus]):
    if len(statuses) == 0:
        return
    table = Table()
    table.add_column("Name")
    table.add_column("Message")
    table.add_column("Is Active")
    for status in statuses:
        table.add_row(status.tag, status.health.message, str(status.health.ok))
    console.print(Text(title, style="bold"))
    console.print(table)
