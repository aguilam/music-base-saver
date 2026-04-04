import tomllib
from pathlib import Path
from fastapi import FastAPI, status, Request, APIRouter, Depends
from fastapi.responses import Response, JSONResponse
from core.library_manager import LibraryManager
from core.schemas import QueryType
from collections import defaultdict
import hashlib
from typing import Annotated
from core.db.models import User
from hmac import compare_digest
from utils.utils import image_mime
from fastapi.middleware.cors import CORSMiddleware
from api.mappers import (
    to_subsonic_album,
    to_subsonic_artist,
    to_subsonic_playlist,
    to_subsonic_song,
    external_album_to_subsonic,
    external_artist_to_subsonic,
    external_track_to_subsonic,
)


async def get_user(
    u: str | None = None,
    t: str | None = None,
    s: str | None = None,
    apiKey: str | None = None,
):
    api_key = apiKey
    username = u
    token = t
    salt = s
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
        user = library_manager.get_user(apiKey=api_key)
        if user is None:
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
        return user
    elif (
        username is not None
        and api_key is None
        and salt is not None
        and token is not None
    ):
        user = library_manager.get_user(username=username)
        if user is None or not (
            compare_digest(
                hashlib.md5((user.password + salt).encode("utf-8")).hexdigest(), token
            )
            and compare_digest(username, user.username)
        ):
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
        return user
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


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
subsonic_router = APIRouter(prefix="/rest", dependencies=[Depends(get_user)])
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


@subsonic_router.get("/stream", status_code=status.HTTP_206_PARTIAL_CONTENT)
def stream_track(request: Request, id: int):
    CHUNK_SIZE = 1024 * 1024
    range_header = request.headers.get("range")
    if not range_header:
        start = 0
        end = start + CHUNK_SIZE
    else:
        range = range_header.replace("bytes=", "").split("-")
        start = int(range[0])
        end = int(range[1]) if range[1] != "" else start + CHUNK_SIZE
    track_bytes = library_manager.stream_track(id, start, end)
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


@subsonic_router.get("/getPlaylists")
def get_user_playlists(user: Annotated[User, Depends(get_user)]):
    user_playlists = library_manager.get_user_playlists(user.id)
    subsonic_playlists = [to_subsonic_playlist(playlist) for playlist in user_playlists]
    return {
        "subsonic-response": {
            "status": "ok",
            "version": "1.16.1",
            "type": "AwesomeServerName",
            "serverVersion": "0.1.3 (tag)",
            "openSubsonic": True,
            "playlists": {"playlist": subsonic_playlists},
        }
    }


@subsonic_router.get("/getPlaylist")
def get_playlist(id: int, user: Annotated[User, Depends(get_user)]):
    playlist = library_manager.get_playlist_by_id(id)
    if playlist is None:
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
    subsonic_playlist = to_subsonic_playlist(playlist)
    tracks = []
    for track in playlist.tracks:
        track_link = next(
            (link.link for link in track.links if link.link_type == "storage"),
            None,
        )
        subsonic_track = to_subsonic_song(track)

        subsonic_track["path"] = track_link

        tracks.append(subsonic_track)
    subsonic_playlist["entry"] = tracks
    return {
        "subsonic-response": {
            "status": "ok",
            "version": "1.16.1",
            "type": "AwesomeServerName",
            "serverVersion": "0.1.3 (tag)",
            "openSubsonic": True,
            "playlist": subsonic_playlist,
        }
    }


@subsonic_router.get("/getStarred2")
def get_user_starred(user: Annotated[User, Depends(get_user)]):
    tracks, albums, artists = library_manager.get_all_user_starred(user.id)
    parsed_tracks = [to_subsonic_song(track) for track in tracks]
    parsed_albums = [to_subsonic_album(album) for album in albums]
    parsed_artist = [to_subsonic_artist(artist) for artist in artists]
    return {
        "subsonic-response": {
            "status": "ok",
            "version": "1.16.1",
            "type": "AwesomeServerName",
            "serverVersion": "0.1.3 (tag)",
            "openSubsonic": True,
            "starred2": {
                "artist": parsed_artist,
                "album": parsed_albums,
                "song": parsed_tracks,
            },
        }
    }


@subsonic_router.get("/getCoverArt")
def get_cover_art(id: str):
    splited_id = id.split("-")
    cover_path = ""
    if len(splited_id) != 2:
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
    if splited_id[0] == "al":
        album = library_manager.get_album_by_id(splited_id[1])
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
        cover_path = album.cover_path
    elif splited_id[0] == "ar":
        artist = library_manager.get_artist_by_id(splited_id[1])
        if artist is None or artist.cover_path is None:
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
        cover_path = artist.cover_path
    else:
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
    splited_path = cover_path.split("///")
    cover_art = library_manager.get_file(splited_path[1], splited_path[0])
    mime = image_mime(cover_art)
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


@subsonic_router.get("/search3")
def local_serch(
    query: str,
    artistCount: int = 20,
    artistOffset: int = 0,
    albumCount: int = 20,
    albumOffset: int = 0,
    songCount: int = 20,
    songOffset: int = 0,
):
    searched = library_manager.local_search(
        query, artistCount, artistOffset, albumCount, albumOffset, songCount, songOffset
    )
    return {
        "subsonic-response": {
            "status": "ok",
            "version": "1.16.1",
            "type": "AwesomeServerName",
            "serverVersion": "0.1.3 (tag)",
            "openSubsonic": True,
            "searchResult3": {
                "artist": [
                    to_subsonic_artist(artist) for artist in searched["artists"]
                ],
                "album": [to_subsonic_album(album) for album in searched["albums"]],
                "song": [to_subsonic_song(track) for track in searched["tracks"]],
            },
        }
    }


@subsonic_router.post("/globalDownload")
def global_download(query: str = None, id: str = None):
    task_id = library_manager.post_download(query=query, id=id)
    return {
        "subsonic-response": {
            "status": "ok",
            "version": "1.16.1",
            "type": "AwesomeServerName",
            "serverVersion": "0.1.3 (tag)",
            "openSubsonic": True,
            "taskId": task_id,
        }
    }


@subsonic_router.get("/checkGlobalDownload")
def check_global_download(id: str):
    download = library_manager.checks_status(id)
    return {
        "subsonic-response": {
            "status": "ok",
            "version": "1.16.1",
            "type": "AwesomeServerName",
            "serverVersion": "0.1.3 (tag)",
            "openSubsonic": True,
            "download": {
                "status": download["status"],
                "progress": download["progress"],
                "result": download.get("result"),
            },
        }
    }


@subsonic_router.get("/globalSearch")
def global_search(
    query: str,
):
    searched = library_manager.global_search(query)
    artists = []
    albums = []
    tracks = []
    for artist in searched["artists"]:
        sub_artist = external_artist_to_subsonic(artist)
        sub_artist["dbId"] = artist["db_id"]
        artists.append(sub_artist)
    for album in searched["albums"]:
        sub_album = external_album_to_subsonic(album)
        sub_album["dbId"] = album["db_id"]
        albums.append(sub_album)
    for track in searched["tracks"]:
        sub_track = external_track_to_subsonic(track)
        sub_track["dbId"] = track["db_id"]
        tracks.append(sub_track)
    return {
        "subsonic-response": {
            "status": "ok",
            "version": "1.16.1",
            "type": "AwesomeServerName",
            "serverVersion": "0.1.3 (tag)",
            "openSubsonic": True,
            "globalSearchResult": {"artist": artists, "album": albums, "song": tracks},
        }
    }


@subsonic_router.get("/getArtist")
def get_artist(id: str):
    if "-" in id:
        artist = library_manager.get_global_object("artist", id)
        parsed_artist = external_artist_to_subsonic(artist)
        parsed_artist["album"] = [
            external_album_to_subsonic(album) for album in artist["albums"]
        ]
    else:
        artist = library_manager.get_artist_by_id(int(id))
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
        parsed_artist = to_subsonic_artist(artist)
        parsed_artist["album"] = [to_subsonic_album(album) for album in artist.albums]
    return {
        "subsonic-response": {
            "status": "ok",
            "version": "1.16.1",
            "type": "AwesomeServerName",
            "serverVersion": "0.1.3 (tag)",
            "openSubsonic": True,
            "artist": parsed_artist,
        }
    }


@subsonic_router.get("/getArtists")
def get_artists():
    artists = library_manager.get_all_artists()
    capitalized_artists = defaultdict(list)
    for artist in artists:
        key = artist.name[0].upper()
        capitalized_artists[key].append(to_subsonic_artist(artist))
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
def get_song(id: str):
    if "-" in id:
        track = library_manager.get_global_object("track", id)
        song = external_track_to_subsonic(track)
    else:
        track = library_manager.get_track_by_id(int(id))
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
        song = to_subsonic_song(track)
        song["path"] = song_link
    return {
        "subsonic-response": {
            "status": "ok",
            "version": "1.16.1",
            "type": "AwesomeServerName",
            "serverVersion": "0.1.3 (tag)",
            "openSubsonic": True,
            "song": song,
        }
    }


@subsonic_router.get("/getAlbum")
def get_album(id: str):
    if "-" in id:
        album = library_manager.get_global_object("album", id)
        parsed_album = external_album_to_subsonic(album)
        parsed_album["song"] = [
            external_track_to_subsonic(track) for track in album["tracks"]
        ]
    else:
        album = library_manager.get_album_by_id(int(id))
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
        parsed_album = to_subsonic_album(album)
        tracks = []
        for track in album.tracks:
            track_link = next(
                (link.link for link in track.links if link.link_type == "storage"), None
            )
            subsonic_track = to_subsonic_song(track)

            subsonic_track["path"] = track_link

            tracks.append(subsonic_track)
        parsed_album["song"] = tracks
    return {
        "subsonic-response": {
            "status": "ok",
            "version": "1.16.1",
            "type": "AwesomeServerName",
            "serverVersion": "0.1.3 (tag)",
            "openSubsonic": True,
            "album": parsed_album,
        }
    }


@subsonic_router.get("/getAlbumList2")
def get_albums():
    albums = library_manager.get_all_albums()
    if albums is None:
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
    parsed_albums = [to_subsonic_album(album) for album in albums]
    return {
        "subsonic-response": {
            "status": "ok",
            "version": "1.16.1",
            "type": "AwesomeServerName",
            "serverVersion": "0.1.3 (tag)",
            "openSubsonic": True,
            "albumList2": {"album": parsed_albums},
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


@subsonic_router.post("/star")
def star(
    user: Annotated[User, Depends(get_user)],
    id: str | None = None,
    albumId: str | None = None,
    artistId: str | None = None,
):
    if id is not None:
        library_manager.star(user.id, id, "track")
    if albumId is not None:
        library_manager.star(user.id, albumId, "album")
    if artistId is not None:
        library_manager.star(user.id, artistId, "artist")
    return {
        "subsonic-response": {
            "status": "ok",
            "version": "0.0.1",
            "type": "Music Saver",
            "serverVersion": "0.0.1 (tag)",
            "openSubsonic": True,
        }
    }


@subsonic_router.post("/unstar")
def unstar(
    user: Annotated[User, Depends(get_user)],
    id: str | None = None,
    albumId: str | None = None,
    artistId: str | None = None,
):
    if id is not None:
        library_manager.unstar(user.id, id, "track")
    if albumId is not None:
        library_manager.unstar(user.id, albumId, "album")
    if artistId is not None:
        library_manager.unstar(user.id, artistId, "artist")
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


app.include_router(subsonic_router)
