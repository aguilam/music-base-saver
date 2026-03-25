import typer
from cli.library_cli import library_app
from cli.search_cli import search_app
from cli.download_cli import download_app
from cli.import_cli import import_app

app = typer.Typer()

app.add_typer(library_app, name="lib")
app.add_typer(search_app, name="search")
app.add_typer(download_app, name="download")
app.add_typer(import_app, name="import")
if __name__ == "__main__":
    app()
