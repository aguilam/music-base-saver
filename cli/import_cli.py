import typer
from core.library_manager import LibraryManager

import_cli = typer.Typer(help="Позволяет импортировать треки в базу")


@import_cli.command("local")
def import_local(move=False):
    library_manager = LibraryManager()
    pass
