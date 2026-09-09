from fastapi.responses import FileResponse
from pathlib import Path
from fastapi.staticfiles import StaticFiles
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from interfaces.base_interface import Interface

BASE_DIR = Path(__file__).resolve().parent / "dist"

app = FastAPI()

app.mount("/assets", StaticFiles(directory=BASE_DIR / "assets"), "assets")


@app.get("/{path:path}")
async def pages(path: str):
    return FileResponse(BASE_DIR / "index.html")


class WebUi(Interface):
    async def start(self):
        port = int(self.config.get("port", 3000))
        host = self.config.get("host", "0.0.0.0")
        app.add_middleware(
            CORSMiddleware,
            allow_origin_regex=r".*",
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        config = uvicorn.Config(app, port=port, host=host)
        server = uvicorn.Server(config)
        await server.serve()
