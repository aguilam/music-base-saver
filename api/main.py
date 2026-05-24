from fastapi import FastAPI, status, Request, APIRouter, Depends
from fastapi.responses import Response, JSONResponse
from core.library_manager import LibraryManager
from collections import defaultdict
import hashlib
from typing import Annotated
from core.schemas.schemas import User
from hmac import compare_digest
from fastapi.middleware.cors import CORSMiddleware
from api.mappers import (
    to_subsonic_album,
    to_subsonic_artist,
    to_subsonic_playlist,
    to_subsonic_song,
    to_subsonic_lyric,
    external_album_to_subsonic,
    external_artist_to_subsonic,
    external_track_to_subsonic,
)
import json
from core.schemas.schemas import Task, DownloadTaskResult, SyncTaskResult


class SubsonicException(Exception):
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message


opensubsonic_error = {
    0: "A generic error.",
    10: "Required parameter is missing.",
    20: "Incompatible Subsonic REST protocol version. Client must upgrade.",
    40: "Wrong username or password.",
    42: "Provided authentication mechanism not supported.",
    43: "Multiple conflicting authentication mechanisms provided.",
    44: "Invalid API key.",
    50: "User is not authorized for the given operation.",
    70: "The requested data was not found.",
}


def raise_subsonic_error(code: int):
    message = opensubsonic_error.get(code, "Error")
    raise SubsonicException(code, message)


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
        raise_subsonic_error(43)
    if api_key is not None and username is None:
        user = library_manager.get_user(apiKey=api_key)
        if user is None:
            raise_subsonic_error(44)
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
            raise_subsonic_error(40)
        return user
    else:
        raise_subsonic_error(10)


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
subsonic_router = APIRouter(prefix="/rest", dependencies=[Depends(get_user)])
library_manager = LibraryManager()


@app.exception_handler(SubsonicException)
async def subsonic_exception_handler(request: Request, exc: SubsonicException):
    return JSONResponse(
        status_code=200,
        content={
            "error": {"code": exc.code, "message": exc.message},
        },
    )


@app.middleware("http")
async def subsonic_middleware(request: Request, call_next):
    response: Response = await call_next(request)
    if not request.url.path.startswith("/rest"):
        return response
    content_type = response.headers.get("content-type", "")
    if not content_type.startswith("application/json"):
        return response

    body = b""
    async for chunk in response.body_iterator:
        body += chunk
    try:
        response_body = json.loads(body)

    except json.JSONDecodeError:
        return response
    status = "failed" if response_body.get("error") else "ok"
    wrapped_body = {
        "subsonic-response": {
            "status": status,
            "version": "1.16.1",
            "type": "MusicSaver",
            "serverVersion": "0.0.1 (tag)",
            "openSubsonic": True,
            **response_body,
        }
    }
    headers = dict(response.headers)
    headers.pop("content-length", None)
    new_response = JSONResponse(
        content=wrapped_body,
        status_code=response.status_code,
        background=response.background,
        headers=headers,
    )

    return new_response


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
def search(query: str, type: str):
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
def stream_track(request: Request, id: str):
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
    if track_bytes is None:
        raise_subsonic_error(70)
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
        "playlists": {"playlist": subsonic_playlists},
    }


@subsonic_router.post("/createPlaylists")
def create_playlist(
    user: Annotated[User, Depends(get_user)],
    songId: list[int],
    name: str | None = None,
    playlistId: int | None = None,
):
    new_playlist = library_manager.create_playlist(user.id, name, songId)
    if new_playlist is None:
        raise_subsonic_error(70)
    subsonic_playlist = to_subsonic_playlist(new_playlist)
    tracks = []
    for track in new_playlist.tracks:
        subsonic_track = to_subsonic_song(track)
        tracks.append(subsonic_track)
    subsonic_playlist["entry"] = tracks
    return {"playlists": subsonic_playlist}


@subsonic_router.delete("/deletePlaylist")
def delete_playlist(id: int, user: Annotated[User, Depends(get_user)]):
    library_manager.delete_playlist(id, user.id)
    return {}


@subsonic_router.post("/changePassword")
def change_password(
    username: str, password: str, user: Annotated[User, Depends(get_user)]
):
    library_manager.update_user(user.id, username, password)
    return {}


@subsonic_router.post("/updateUser")
def update_user(
    username: str,
    user: Annotated[User, Depends(get_user)],
    adminRole: bool | None = None,
    password: str | None = None,
):
    library_manager.update_user(user.id, username, password, adminRole)
    return {}


@subsonic_router.post("/createUser")
def create_user(username: str, password: str, email: str):
    library_manager.create_user(username, password, email)
    return {}


@subsonic_router.get("/getPlaylist")
def get_playlist(id: int, user: Annotated[User, Depends(get_user)]):
    playlist = library_manager.get_playlist_by_id(id)
    if playlist is None:
        raise_subsonic_error(70)
    subsonic_playlist = to_subsonic_playlist(playlist)
    tracks = []
    for track in playlist.tracks:
        subsonic_track = to_subsonic_song(track)
        tracks.append(subsonic_track)
    subsonic_playlist["entry"] = tracks
    return {
        "playlist": subsonic_playlist,
    }


@subsonic_router.get("/getStarred2")
def get_user_starred(user: Annotated[User, Depends(get_user)]):
    tracks, albums, artists = library_manager.get_all_user_starred(user.id)
    parsed_tracks = [to_subsonic_song(track) for track in tracks]
    parsed_albums = [to_subsonic_album(album) for album in albums]
    parsed_artist = [to_subsonic_artist(artist) for artist in artists]
    return {
        "starred2": {
            "artist": parsed_artist,
            "album": parsed_albums,
            "song": parsed_tracks,
        },
    }


@subsonic_router.get("/getCoverArt")
def get_cover_art(id: int):
    cover_art = library_manager.get_cover_art(id)
    if cover_art is None:
        raise_subsonic_error(70)
    return Response(content=cover_art.content, media_type=cover_art.mime)


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
        "searchResult3": {
            "artist": [to_subsonic_artist(artist) for artist in searched.artists],
            "album": [to_subsonic_album(album) for album in searched.albums],
            "song": [to_subsonic_song(track) for track in searched.tracks],
        },
    }


@subsonic_router.post("/globalDownload")
def global_download(query: str = None, id: str = None):
    task_id = library_manager.post_task(query=query, object_id=id)
    return {
        "taskId": task_id,
    }


@subsonic_router.get("/checkGlobalDownload")
def check_global_download(id: str):
    download: Task[DownloadTaskResult] | None = library_manager.get_task(id)
    if download is None:
        raise_subsonic_error(70)
    download_response = {
        "download": {
            "status": download.status,
            "progress": download.progress,
        }
    }
    if download.result:
        download_response["result"] = (download.result.__dict__,)
    return download_response


@subsonic_router.get("/globalSearch")
def global_search(
    query: str,
):
    searched = library_manager.global_search(query)
    artists = []
    albums = []
    tracks = []
    for artist in searched.artists:
        sub_artist = external_artist_to_subsonic(artist)
        sub_artist["dbId"] = artist["db_id"]
        artists.append(sub_artist)
    for album in searched.albums:
        sub_album = external_album_to_subsonic(album)
        sub_album["dbId"] = album["db_id"]
        albums.append(sub_album)
    for track in searched.tracks:
        sub_track = external_track_to_subsonic(track)
        sub_track["dbId"] = track["db_id"]
        tracks.append(sub_track)
    return {
        "globalSearchResult": {"artist": artists, "album": albums, "song": tracks},
    }


@subsonic_router.get("/getArtist")
def get_artist(id: str):
    if "-" in id:
        artist = library_manager.get_global_object("artist", id)
        parsed_artist = external_artist_to_subsonic(artist)
        parsed_artist["album"] = [
            external_album_to_subsonic(album) for album in artist.albums
        ]
    else:
        artist = library_manager.get_artist_by_id(int(id))
        if artist is None:
            raise_subsonic_error(70)
        parsed_artist = to_subsonic_artist(artist)
        parsed_artist["album"] = [to_subsonic_album(album) for album in artist.albums]
    return {
        "artist": parsed_artist,
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
        "artists": {
            "ignoredArticles": "",
            "index": index,
        },
    }


@subsonic_router.get("/getSong")
def get_song(id: str):
    if "-" in id:
        track = library_manager.get_global_object("track", id)
        song = external_track_to_subsonic(track)
    else:
        track = library_manager.get_track_by_id(int(id))
        if track is None:
            raise_subsonic_error(70)
        song_link = next(
            (link.link for link in track.links if link.link_type == "storage"), None
        )
        song = to_subsonic_song(track)
        song["path"] = song_link
    return {
        "song": song,
    }


@subsonic_router.get("/getAlbum")
def get_album(id: str):
    if "-" in id:
        album = library_manager.get_global_object("album", id)
        parsed_album = external_album_to_subsonic(album)
        parsed_album["song"] = [
            external_track_to_subsonic(track) for track in album.tracks
        ]
    else:
        album = library_manager.get_album_by_id(int(id))
        if album is None:
            raise_subsonic_error(70)
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
        "album": parsed_album,
    }


@subsonic_router.get("/getAlbumList2")
def get_albums():
    albums = library_manager.get_all_albums()
    if albums is None:
        raise_subsonic_error(70)
    parsed_albums = [to_subsonic_album(album) for album in albums]
    return {
        "albumList2": {"album": parsed_albums},
    }


@subsonic_router.get("/ping")
def ping():
    return {}


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
    return {}


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
    return {}


@subsonic_router.post("/scrobble")
def unstar(id: int, time: int | None = None, submission: bool | None = True):
    if submission:
        library_manager.scrobble(id, time)
    else:
        library_manager.post_now_playing(id)
    return {}


@subsonic_router.get("/getLyrics")
def get_lyrics(title: str, artist: str | None = None):
    track = library_manager.get_track_by_title(title)
    lyrics = library_manager.get_lyrics(track.id)
    lyric = next((lyric for lyric in lyrics if lyric.is_synced == False), None)
    return {
        "lyrics": {
            "artist": lyric.artist,
            "title": lyric.title,
            "value": lyric.plain_text,
        },
    }


@subsonic_router.get("/getLyricsBySongId")
def get_lyrics(id: int, enhanced: bool | None = False):
    lyrics = library_manager.get_lyrics(id)
    sub_lyrics = [to_subsonic_lyric(lyric) for lyric in lyrics]
    return {
        "lyricsList": {"structuredLyrics": sub_lyrics},
    }


@subsonic_router.get("/getTopSongs")
def get_artist_top_songs(artist: str, count: int | None = 50):
    tracks = library_manager.get_artist_top_songs(artist, count)
    artist_songs = [to_subsonic_song(track) for track in tracks]
    return {
        "topSongs": {"song": artist_songs},
    }


@subsonic_router.get("/getGenres")
def get_genres():
    genres = library_manager.get_genres()
    sub_genres = []
    for genre in genres:
        sub_genres.append(
            {
                "songCount": genre["track_count"],
                "albumCount": genre["album_count"],
                "value": genre["name"],
            }
        )
    return {
        "genres": {"genre": sub_genres},
    }


@subsonic_router.get("/getMoods")
def get_moods():
    moods = library_manager.get_moods()
    sub_moods = []
    for mood in moods:
        sub_moods.append(
            {
                "songCount": mood["track_count"],
                "albumCount": mood["album_count"],
                "value": mood["name"],
            }
        )
    return {
        "moods": {"mood": sub_moods},
    }


@subsonic_router.get("/deleteUser")
def delete_user(username: str, user: Annotated[User, Depends(get_user())]):
    result = library_manager.delete_user_by_username(username, user.id)
    if result is None:
        raise_subsonic_error(50)
    elif result == 0:
        raise_subsonic_error(70)
    return {}


@subsonic_router.get("/download")
def download_to_user():
    return {"hello world"}


@subsonic_router.get("/startScan")
def start_scan():
    library_manager.post_task(sync_id="sub")
    return {
        "scanStatus": {"scanning": True, "count": 0},
    }


@subsonic_router.get("/scanStatus")
def scan_status():
    task: Task[SyncTaskResult] | None = library_manager.get_task("sub")
    if task is None:
        raise_subsonic_error(70)
    is_scanning = True if task.status == "processing" else False
    return {
        "scanStatus": {"scanning": is_scanning, "count": task.result.added},
    }


@subsonic_router.get("/getLicense")
def get_license():
    return {
        "license": {
            "valid": True,
            "email": "demo@demo.org",
            "licenseExpires": "2099-01-01T00:00:00",
            "trialExpires": "2099-01-01T00:00:00",
        }
    }


app.include_router(subsonic_router)
