import typer
from core.library_manager import LibraryManager

import_app = typer.Typer(help="Позволяет импортировать треки в базу")


@import_app.command("from")
def import_local(importer_tag: str):
    library_manager = LibraryManager()
    library_manager.import_library(importer_tag=importer_tag)
    pass
