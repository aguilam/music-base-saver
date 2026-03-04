import tomllib
from pathlib import Path
from fastapi import APIRouter
from fastapi import FastAPI, status, Request
from fastapi.responses import Response
from core.library_manager import LibraryManager
from core.schemas import QueryType
from collections import defaultdict

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


@router.get("/getArtist")
def get_artist(id: int):
    artist = library_manager.get_artist_by_id(id)
    albums = []
    for album in artist.albums:
        title = album.title
        albums.append(
            {
                "id": album.id,
                "parent": album.artist_id,
                "album": title,
                "title": title,
                "name": title,
                "isDir": True,
                "coverArt": "al-200000002",
                "songCount": len(album.tracks),
                "created": "2021-02-23T04:24:48+00:00",
                "artistId": album.artist_id,
                "artist": album.artist_rel.name,
                "duration": 0,
            }
        )
    return {
        "subsonic-response": {
            "status": "ok",
            "version": "1.16.1",
            "type": "AwesomeServerName",
            "serverVersion": "0.1.3 (tag)",
            "openSubsonic": True,
            "artist": {
                "id": artist.id,
                "name": artist.name,
                "albumCount": len(artist.albums),
                "artistImageUrl": "https://demo.org/image.jpg",
                "album": albums,
            },
        }
    }


@router.get("/getArtists")
def get_artists():
    artists = library_manager.get_all_artists()
    capitalized_artists = defaultdict(list)
    for artist in artists:
        key = artist.name[0].upper()
        capitalized_artists[key].append(
            {
                "id": artist.id,
                "name": artist.name,
                "coverArt": "test",
                "albumCount": len(artist.albums),
            }
        )
    sorted_artists = dict(sorted(capitalized_artists.items()))
    index = []
    for k, v in sorted_artists.items():
        index.append({"name": k, "artist": v})
    return {
        "subsonic-response": {
            "status": "ok",
            "version": "1.16.1",
            "type": "AwesomeServerName",
            "serverVersion": "0.1.3 (tag)",
            "openSubsonic": True,
            "artists": {
                "ignoredArticles": "The An A Die Das Ein Eine Les Le La",
                "index": index,
            },
        }
    }


@router.get("/getSong")
def get_song(id: int):
    track = library_manager.get_track_by_id(id)
    song_link = next(
        (link.link for link in track.links if link.link_type == "storage"), None
    )
    return {
        "subsonic-response": {
            "status": "ok",
            "version": "1.16.1",
            "type": "AwesomeServerName",
            "serverVersion": "0.1.3 (tag)",
            "openSubsonic": True,
            "song": {
                "id": track.id,
                "parent": track.album_id,
                "isDir": False,
                "title": track.title,
                "album": track.album.title,
                "artist": track.album.artist_rel.name,
                "coverArt": "mf-082f435a363c32c57d5edb6a678a28d4_6410b3ce",
                "duration": track.length,
                "path": song_link,
                "created": "2023-03-14T17:51:22.112827504Z",
                "albumId": track.album_id,
                "artistId": track.album.artist_id,
                "type": "music",
                "mediaType": "song",
                "isVideo": False,
            },
        }
    }


@router.get("/getAlbum")
def get_album(id: int):
    album = library_manager.get_album_by_id(id)
    songs = []
    album_title = album.title
    for song in album.tracks:
        song_link = next(
            (link.link for link in song.links if link.link_type == "storage"), None
        )
        songs.append(
            {
                "id": song.id,
                "parent": album.id,
                "title": song.title,
                "isDir": False,
                "isVideo": False,
                "type": "music",
                "albumId": album.id,
                "album": album_title,
                "artistId": album.artist_id,
                "artist": album.artist_rel.name,
                "coverArt": "300000116",
                "duration": song.length,
                "path": song_link,
            }
        )
    return {
        "subsonic-response": {
            "status": "ok",
            "version": "1.16.1",
            "type": "AwesomeServerName",
            "serverVersion": "0.1.3 (tag)",
            "openSubsonic": True,
            "album": {
                "id": album.id,
                "parent": album.artist_id,
                "album": album_title,
                "title": album_title,
                "name": album_title,
                "isDir": True,
                "coverArt": "al-200000021",
                "songCount": len(album.tracks),
                "created": "2021-07-22T02:09:31+00:00",
                "duration": 0,
                "artistId": album.artist_id,
                "artist": album.artist_rel.name,
                "song": songs,
            },
        }
    }


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
