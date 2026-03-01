import tomllib
from pathlib import Path
from fastapi import APIRouter
from fastapi import FastAPI, status, Request
from fastapi.responses import Response
from core.library_manager import LibraryManager
from core.schemas import QueryType

app = FastAPI()
router = APIRouter(prefix="/rest")
toml_file_path = Path("config.toml")
with toml_file_path.open("rb") as config_file:
    config = tomllib.load(config_file)

library_manager = LibraryManager()


@app.get("/")
def root():
    return {"Hello World"}


@app.patch("/config")
def change_configuration():
    return {"Hello World"}


@app.get("/search")
def search(query: str, type: QueryType):
    search_results = library_manager.search(query, type)
    return search_results


@app.get("/tracks/download/status")
def check_status():
    return {"hello world"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/track/download")
def download(query: str):
    downloaded_path = library_manager.download(query)
    return downloaded_path


@app.get("/tracks/get")
def get_tracks():
    tracks = library_manager.get_all_tracks()
    return tracks


@router.get("/track/stream", status_code=status.HTTP_206_PARTIAL_CONTENT)
def stream_track(request: Request, track_id: int):
    CHUNK_SIZE = 1024 * 1024
    range_header = request.headers.get("range")
    if not range_header:
        start = 0
        end = start + CHUNK_SIZE
    else:
        range = range_header.replace("bytes=", "").split("-")
        start = int(range[0])
        end = int(range[1]) if range[1] != "" else start + CHUNK_SIZE
    track_bytes = library_manager.stream_track(track_id, start, end)
    headers = {
        "content-length": str(len(track_bytes["bytes"])),
        "content-range": f"bytes {start}-{track_bytes['end_bytes']}/{track_bytes['file_size']}",
        "Accept-Ranges": "bytes",
    }
    return Response(
        content=track_bytes["bytes"],
        status_code=status.HTTP_206_PARTIAL_CONTENT,
        headers=headers,
        media_type="application/octet-stream",
    )


@router.get("/getCoverArt")
def get_cover_art():
    return {"hello world"}


@router.get("/getMusicFolders")
def get_music_folders():
    return {"hello world"}


@router.get("/getIndexes")
def get_indexes():
    return {"hello world"}


@router.get("/getMusicDirectory")
def get_music_directory():
    return {"hello world"}


@router.get("/ping")
def ping():
    return {
        "subsonic-response": {
            "status": "ok",
            "version": "0.0.1",
            "type": "Music Saver",
            "serverVersion": "0.0.1 (tag)",
            "openSubsonic": True,
        }
    }


@router.get("/getLyrics")
def get_lyrics():
    return {"hello world"}


@router.get("/download")
def download_to_user():
    return {"hello world"}


@router.get("/startScan")
def start_scan():
    return {"hello world"}


@router.get("/scanStatus")
def scan_status():
    return {"hello world"}


@router.get("/getLicense")
def get_license():
    return {
        "subsonic-response": {
            "status": "ok",
            "version": "1.16.1",
            "type": "Music Saver",
            "serverVersion": "0.0.1 (tag)",
            "openSubsonic": True,
            "license": {
                "valid": True,
                "email": "demo@demo.org",
                "licenseExpires": "2099-01-01T00:00:00",
                "trialExpires": "2099-01-01T00:00:00",
            },
        }
    }
