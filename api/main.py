import tomllib
from pathlib import Path
from fastapi import FastAPI, status, Request, APIRouter
from fastapi.responses import Response, JSONResponse
from core.library_manager import LibraryManager
from core.schemas import QueryType
from collections import defaultdict
import hashlib
from hmac import compare_digest
import magic

app = FastAPI()
subsonic_router = APIRouter(prefix="/rest")
toml_file_path = Path("config.toml")
with toml_file_path.open("rb") as config_file:
    config = tomllib.load(config_file)

library_manager = LibraryManager()


@app.get("/")
def root():
    return {"Hello World"}


@app.post("/login")
def login():
    return {"Hello world"}


@app.get("/config")
def change_configuration():
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


@subsonic_router.get("/track/stream", status_code=status.HTTP_206_PARTIAL_CONTENT)
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


@subsonic_router.get("/getCoverArt")
def get_cover_art(id: int):
    album = library_manager.get_album_by_id(id)
    if album is None or album.cover_path is None:
        return {
            "subsonic-response": {
                "status": "failed",
                "version": "1.16.1",
                "type": "AwesomeServerName",
                "serverVersion": "0.1.3 (tag)",
                "openSubsonic": True,
                "error": {
                    "code": 70,
                    "message": "The requested data was not found",
                },
            }
        }
    splited_path = album.cover_path.split("///")
    cover_art = library_manager.get_file(splited_path[1], splited_path[0])
    mime = magic.from_buffer(cover_art, mime=True)
    return Response(content=cover_art, media_type=mime)


@subsonic_router.get("/getMusicFolders")
def get_music_folders():
    return {"hello world"}


@subsonic_router.get("/getIndexes")
def get_indexes():
    return {"hello world"}


@subsonic_router.get("/getMusicDirectory")
def get_music_directory():
    return {"hello world"}


@subsonic_router.get("/getArtist")
def get_artist(id: int):
    artist = library_manager.get_artist_by_id(id)
    if artist is None:
        return {
            "subsonic-response": {
                "status": "failed",
                "version": "1.16.1",
                "type": "AwesomeServerName",
                "serverVersion": "0.1.3 (tag)",
                "openSubsonic": True,
                "error": {
                    "code": 70,
                    "message": "The requested data was not found",
                },
            }
        }
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
                "coverArt": album.cover_path,
                "songCount": len(album.tracks),
                "created": album.created_at,
                "artistId": album.artist_id,
                "artist": album.artist_rel.name,
                "duration": album.duration,
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


@subsonic_router.get("/getArtists")
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


@subsonic_router.get("/getSong")
def get_song(id: int):
    track = library_manager.get_track_by_id(id)
    if track is None:
        return {
            "subsonic-response": {
                "status": "failed",
                "version": "1.16.1",
                "type": "AwesomeServerName",
                "serverVersion": "0.1.3 (tag)",
                "openSubsonic": True,
                "error": {
                    "code": 70,
                    "message": "The requested data was not found",
                },
            }
        }
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
                "coverArt": track.album.cover_path,
                "duration": track.length,
                "path": song_link,
                "created": track.created_at,
                "albumId": track.album_id,
                "artistId": track.album.artist_id,
                "type": "music",
                "mediaType": "song",
                "isVideo": False,
            },
        }
    }


@subsonic_router.get("/getAlbum")
def get_album(id: int):
    album = library_manager.get_album_by_id(id)
    if album is None:
        return {
            "subsonic-response": {
                "status": "failed",
                "version": "1.16.1",
                "type": "AwesomeServerName",
                "serverVersion": "0.1.3 (tag)",
                "openSubsonic": True,
                "error": {
                    "code": 70,
                    "message": "The requested data was not found",
                },
            }
        }
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
                "coverArt": album.cover_path,
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
                "coverArt": album.cover_path,
                "songCount": len(album.tracks),
                "created": album.created_at,
                "duration": album.duration,
                "artistId": album.artist_id,
                "artist": album.artist_rel.name,
                "song": songs,
            },
        }
    }


@subsonic_router.get("/ping")
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


@subsonic_router.get("/getLyrics")
def get_lyrics():
    return {"hello world"}


@subsonic_router.get("/download")
def download_to_user():
    return {"hello world"}


@subsonic_router.get("/startScan")
def start_scan():
    scan = library_manager.sync()
    all_objects = scan["deleted_count"] + scan["added_count"]
    return {
        "subsonic-response": {
            "status": "ok",
            "version": "1.16.1",
            "type": "AwesomeServerName",
            "serverVersion": "0.1.3 (tag)",
            "openSubsonic": True,
            "scanStatus": {"scanning": False, "count": all_objects},
        }
    }


@subsonic_router.get("/scanStatus")
def scan_status():
    return {"hello world"}


@subsonic_router.get("/getLicense")
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


@subsonic_router.middleware("http")
async def login_middleware(request: Request, call_next):
    params = request.query_params
    api_key = params.get("api_key")
    username = params.get("u")
    token = params.get("t")
    salt = params.get("s")
    user_password = config["api"]["password"]
    user_username = config["api"]["username"]
    user_api_key = config["api"]["api_key"]
    if username is not None and api_key is not None:
        return JSONResponse(
            {
                "subsonic-response": {
                    "status": "failed",
                    "version": "1.16.1",
                    "type": "AwesomeServerName",
                    "serverVersion": "0.1.3 (tag)",
                    "openSubsonic": True,
                    "error": {
                        "code": 43,
                        "message": "Multiple conflicting authentication mechanisms provided",
                    },
                }
            }
        )
    if api_key is not None and username is None:
        if compare_digest(api_key, user_api_key):
            return await call_next(request)
        else:
            return JSONResponse(
                {
                    "subsonic-response": {
                        "status": "failed",
                        "version": "1.16.1",
                        "type": "AwesomeServerName",
                        "serverVersion": "0.1.3 (tag)",
                        "openSubsonic": True,
                        "error": {"code": 44, "message": "Invalid API key"},
                    }
                }
            )
    elif (
        username is not None
        and api_key is None
        and user_password is not None
        and salt is not None
        and token is not None
    ):
        if compare_digest(
            hashlib.md5((user_password + salt).encode("utf-8")).hexdigest(), token
        ) and compare_digest(username, user_username):
            return await call_next(request)
        else:
            return JSONResponse(
                {
                    "subsonic-response": {
                        "status": "failed",
                        "version": "1.16.1",
                        "type": "AwesomeServerName",
                        "serverVersion": "0.1.3 (tag)",
                        "openSubsonic": True,
                        "error": {"code": 40, "message": "Wrong username or password"},
                    }
                }
            )
    else:
        return JSONResponse(
            {
                "subsonic-response": {
                    "status": "failed",
                    "version": "1.16.1",
                    "type": "AwesomeServerName",
                    "serverVersion": "0.1.3 (tag)",
                    "openSubsonic": True,
                    "error": {
                        "code": 10,
                        "message": "Required parameter is missing",
                    },
                }
            }
        )


app.include_subsonic_router(subsonic_router)
