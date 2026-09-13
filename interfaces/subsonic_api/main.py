import hashlib
import json
from collections import defaultdict
from hmac import compare_digest
from typing import Annotated

import uvicorn
from fastapi import APIRouter, Depends, FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, StreamingResponse

from core.errors import BaseError
from core.responses import FullAlbumResponse, FullArtistResponse, FullTrackResponse
from core.responses.mappers import to_short_user_response
from core.schemas import StoredUser as User
from interfaces import Interface
from interfaces.subsonic_api import admin_router
from interfaces.subsonic_api.mappers import (
    album_track_to_subsonic_song,
    playlist_track_to_subsonic_song,
    to_subsonic_album,
    to_subsonic_artist,
    to_subsonic_lyric,
    to_subsonic_playlist,
    to_subsonic_song,
)
from interfaces.subsonic_api.utils import (
    CurrentLibrary,
    SubsonicException,
    check_subsonic_error,
    raise_subsonic_error,
)


def get_user(
    library_manager: CurrentLibrary,
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
        key = library_manager.check_api_key_availability(api_key)
        if isinstance(key, BaseError):
            raise_subsonic_error(44)
        user = library_manager.get_user(user_id=key.user_id)
        if user is None:
            raise_subsonic_error(70)
        return user
    elif (
        username is not None
        and api_key is None
        and salt is not None
        and token is not None
    ):
        user = library_manager.get_internal_user(username=username)
        if user is None or isinstance(user, BaseError):
            raise_subsonic_error(40)
        if not (
            compare_digest(
                hashlib.md5((user.password + salt).encode("utf-8")).hexdigest(),
                token,
            )
            and compare_digest(username, user.username)
        ):
            raise_subsonic_error(40)
        return to_short_user_response(user)
    else:
        raise_subsonic_error(10)


subsonic_router = APIRouter(
    prefix="/rest", dependencies=[Depends(get_user)], tags=["OpenSubsonic"]
)


async def subsonic_exception_handler(request: Request, exc: Exception):
    if not isinstance(exc, SubsonicException):
        raise exc
    return JSONResponse(
        status_code=200,
        content={
            "error": {"code": exc.code, "message": exc.message},
        },
    )


async def subsonic_middleware(request: Request, call_next):
    response: Response = await call_next(request)
    if not request.url.path.startswith("/rest"):
        return response
    content_type = response.headers.get("content-type", "")
    if not content_type.startswith("application/json"):
        return response

    body: bytes = b""
    if hasattr(response, "body_iterator"):
        async for chunk in response.body_iterator:
            if isinstance(chunk, str):
                body += chunk.encode("utf-8")
            else:
                body += bytes(chunk)
    else:
        body = (
            response.body if isinstance(response.body, bytes) else bytes(response.body)
        )
    try:
        response_body = json.loads(body)
    except json.JSONDecodeError:
        return Response(
            content=body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
        )

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


@subsonic_router.get("/stream.view")
@subsonic_router.get("/stream")
def stream_track(library_manager: CurrentLibrary, request: Request, id: str):
    metadata = check_subsonic_error(library_manager.get_file_metadata(id))
    range_header = request.headers.get("range")
    if not range_header:
        start = 0
        end = metadata.file_size - 1
        response_status = status.HTTP_200_OK
        headers = {
            "Content-Length": str(metadata.file_size),
            "Accept-Ranges": "bytes",
        }
    else:
        range = range_header.replace("bytes=", "").split("-")
        start = int(range[0])
        end = (
            int(range[1])
            if len(range) > 1 and range[1] != ""
            else metadata.file_size - 1
        )
        response_status = status.HTTP_206_PARTIAL_CONTENT
        content_length = end - start + 1
        headers = {
            "Content-Length": str(content_length),
            "Content-Range": f"bytes {start}-{end}/{metadata.file_size}",
            "Accept-Ranges": "bytes",
        }
    return StreamingResponse(
        check_subsonic_error(library_manager.stream_track(id, start, end)),
        headers=headers,
        status_code=response_status,
    )


@subsonic_router.get("/getPlaylists.view")
@subsonic_router.get("/getPlaylists")
def get_user_playlists(
    library_manager: CurrentLibrary, user: Annotated[User, Depends(get_user)]
):
    user_playlists = library_manager.get_user_playlists(user.id)
    subsonic_playlists = [to_subsonic_playlist(playlist) for playlist in user_playlists]
    return {
        "playlists": {"playlist": subsonic_playlists},
    }


@subsonic_router.post("/createPlaylists")
def create_playlist(
    library_manager: CurrentLibrary,
    user: Annotated[User, Depends(get_user)],
    songId: list[int],
    name: str | None = None,
    playlistId: int | None = None,
):
    if name is not None:
        new_playlist = check_subsonic_error(
            library_manager.create_playlist(user.id, name, songId)
        )
    elif playlistId is not None:
        new_playlist = check_subsonic_error(
            library_manager.update_playlist(
                playlist_id=playlistId, user_id=user.id, track_ids=songId, title=name
            )
        )
    subsonic_playlist = to_subsonic_playlist(new_playlist)
    tracks = []
    for track in new_playlist.tracks:
        subsonic_track = playlist_track_to_subsonic_song(track)
        tracks.append(subsonic_track)
    subsonic_playlist["entry"] = tracks
    return {"playlists": subsonic_playlist}


@subsonic_router.delete("/deletePlaylist")
def delete_playlist(
    library_manager: CurrentLibrary,
    id: int,
    user: Annotated[User, Depends(get_user)],
):
    check_subsonic_error(library_manager.delete_playlist(id))
    return {}


@subsonic_router.post("/changePassword")
def change_password(
    library_manager: CurrentLibrary,
    username: str,
    password: str,
    user: Annotated[User, Depends(get_user)],
):
    library_manager.update_user_by_username(
        acting_user_id=user.id, current_username=username, new_password=password
    )
    return {}


@subsonic_router.post("/updateUser")
def update_user(
    library_manager: CurrentLibrary,
    username: str,
    user: Annotated[User, Depends(get_user)],
    adminRole: bool | None = None,
    password: str | None = None,
):
    check_subsonic_error(
        library_manager.update_user_by_username(
            acting_user_id=user.id,
            current_username=username,
            new_password=password,
            set_is_admin=adminRole,
        )
    )
    return {}


@subsonic_router.post("/createUser")
def create_user(
    library_manager: CurrentLibrary, username: str, password: str, email: str
):
    library_manager.create_user(username, password, email)
    return {}


@subsonic_router.get("/getPlaylist")
@subsonic_router.get("/getPlaylist.view")
def get_playlist(
    library_manager: CurrentLibrary, id: int, user: Annotated[User, Depends(get_user)]
):
    playlist = check_subsonic_error(library_manager.get_playlist_by_id(id))
    subsonic_playlist = to_subsonic_playlist(playlist)
    tracks = []
    for track in playlist.tracks:
        subsonic_track = playlist_track_to_subsonic_song(track)
        tracks.append(subsonic_track)
    subsonic_playlist["entry"] = tracks
    return {
        "playlist": subsonic_playlist,
    }


@subsonic_router.get("/getStarred2")
@subsonic_router.get("/getStarred2.view")
def get_user_starred(
    library_manager: CurrentLibrary, user: Annotated[User, Depends(get_user)]
):
    tracks, albums, artists = check_subsonic_error(
        library_manager.get_all_user_starred(user.id)
    )
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


@subsonic_router.get("/getCoverArt.view")
@subsonic_router.get("/getCoverArt")
def get_cover_art(library_manager: CurrentLibrary, id: int, response: Response):
    cover_art = check_subsonic_error(library_manager.get_cover_art(id))
    response.headers["Cache-Control"] = "public, max-age=3600"
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


@subsonic_router.get("/search3.view")
@subsonic_router.get("/search3")
def local_serch(
    library_manager: CurrentLibrary,
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
def global_download(
    library_manager: CurrentLibrary, query: str | None = None, id: str | None = None
):
    task_id = library_manager.download(query=query, object_id=id)
    return {
        "taskId": task_id,
    }


@subsonic_router.get("/checkGlobalDownload")
def check_global_download(library_manager: CurrentLibrary, id: str):
    download = check_subsonic_error(library_manager.get_download_task(id))
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
    library_manager: CurrentLibrary,
    query: str,
):
    searched = check_subsonic_error(library_manager.global_search(query))
    artists = []
    albums = []
    tracks = []
    for artist in searched.artists:
        sub_artist = to_subsonic_artist(artist)
        artists.append(sub_artist)
    for album in searched.albums:
        sub_album = to_subsonic_album(album)
        albums.append(sub_album)
    for track in searched.tracks:
        sub_track = to_subsonic_song(track)
        tracks.append(sub_track)
    return {
        "globalSearchResult": {"artist": artists, "album": albums, "song": tracks},
    }


@subsonic_router.get("/getArtist.view")
@subsonic_router.get("/getArtist")
def get_artist(library_manager: CurrentLibrary, id: str):
    artist: FullArtistResponse
    if "-" in id:
        artist = check_subsonic_error(library_manager.get_global_object("artist", id))
    else:
        artist = check_subsonic_error(library_manager.get_artist_by_id(int(id)))
    parsed_artist = to_subsonic_artist(artist)
    parsed_artist["album"] = [to_subsonic_album(album) for album in artist.albums]
    return {
        "artist": parsed_artist,
    }


@subsonic_router.get("/getArtists.view")
@subsonic_router.get("/getArtists")
def get_artists(library_manager: CurrentLibrary):
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
def get_song(library_manager: CurrentLibrary, id: str):
    track: FullTrackResponse
    if "-" in id:
        track = check_subsonic_error(library_manager.get_global_object("track", id))
    else:
        track = check_subsonic_error(library_manager.get_track_by_id(int(id)))
    song = to_subsonic_song(track)
    return {
        "song": song,
    }


@subsonic_router.get("/getAlbum.view")
@subsonic_router.get("/getAlbum")
def get_album(library_manager: CurrentLibrary, id: str):
    album: FullAlbumResponse
    if "-" in id:
        album = check_subsonic_error(library_manager.get_global_object("album", id))
    else:
        album = check_subsonic_error(library_manager.get_album_by_id(int(id)))
    parsed_album = to_subsonic_album(album)
    parsed_album["song"] = [
        album_track_to_subsonic_song(track, album.cover_id) for track in album.tracks
    ]
    return {
        "album": parsed_album,
    }


@subsonic_router.get("/getAlbumList2.view")
@subsonic_router.get("/getAlbumList2")
def get_albums(library_manager: CurrentLibrary, size: int = 10, offset: int = 0):
    albums = library_manager.get_all_albums(size, offset)
    if len(albums) == 0:
        raise_subsonic_error(70)
    parsed_albums = [to_subsonic_album(album) for album in albums]
    return {
        "albumList2": {"album": parsed_albums},
    }


@subsonic_router.get("/ping")
@subsonic_router.get("/ping.view")
def ping():
    return {}


@subsonic_router.get("/star.view")
@subsonic_router.post("/star.view")
@subsonic_router.get("/star")
@subsonic_router.post("/star")
def star(
    library_manager: CurrentLibrary,
    user: Annotated[User, Depends(get_user)],
    id: int | None = None,
    albumId: int | None = None,
    artistId: int | None = None,
):
    if id is not None:
        library_manager.star(user.id, id, "track")
    if albumId is not None:
        library_manager.star(user.id, albumId, "album")
    if artistId is not None:
        library_manager.star(user.id, artistId, "artist")
    return {}


@subsonic_router.get("/unstar.view")
@subsonic_router.post("/unstar.view")
@subsonic_router.get("/unstar")
@subsonic_router.post("/unstar")
def unstar(
    library_manager: CurrentLibrary,
    user: Annotated[User, Depends(get_user)],
    id: int | None = None,
    albumId: int | None = None,
    artistId: int | None = None,
):
    if id is not None:
        library_manager.unstar(user.id, id, "track")
    if albumId is not None:
        library_manager.unstar(user.id, albumId, "album")
    if artistId is not None:
        library_manager.unstar(user.id, artistId, "artist")
    return {}


@subsonic_router.post("/scrobble")
@subsonic_router.post("/scrobble.view")
@subsonic_router.get("/scrobble")
@subsonic_router.get("/scrobble.view")
def scrobble(
    library_manager: CurrentLibrary,
    user: Annotated[User, Depends(get_user)],
    id: int,
    time: int | None = None,
    submission: bool | None = True,
):
    if submission:
        library_manager.scrobble(id, user.id, time)
    else:
        library_manager.post_now_playing(id, user.id)
    return {}


@subsonic_router.get("/getLyrics")
@subsonic_router.get("/getLyrics.view")
def get_lyrics(library_manager: CurrentLibrary, title: str, artist: str | None = None):
    track = check_subsonic_error(library_manager.get_track_by_title(title))
    lyrics = check_subsonic_error(library_manager.get_lyrics(track.id))
    lyric = next((lyric for lyric in lyrics if not lyric.is_synced), None)
    if lyric is None:
        raise_subsonic_error(70)
    return {
        "lyrics": {
            "artist": lyric.artist,
            "title": lyric.title,
            "value": lyric.plain_text,
        },
    }


@subsonic_router.get("/getLyricsBySongId")
@subsonic_router.get("/getLyricsBySongId.view")
def get_lyrics_by_song(
    library_manager: CurrentLibrary, id: int, enhanced: bool | None = False
):
    lyrics = check_subsonic_error(library_manager.get_lyrics(id))
    sub_lyrics = [to_subsonic_lyric(lyric) for lyric in lyrics]
    return {
        "lyricsList": {"structuredLyrics": sub_lyrics},
    }


@subsonic_router.get("/getTopSongs")
@subsonic_router.get("/getTopSongs.view")
def get_artist_top_songs(library_manager: CurrentLibrary, artist: str, count: int = 50):
    tracks = check_subsonic_error(library_manager.get_artist_top_tracks(artist, count))
    artist_songs = [to_subsonic_song(track) for track in tracks]
    return {
        "topSongs": {"song": artist_songs},
    }


@subsonic_router.get("/getGenres.view")
@subsonic_router.get("/getGenres")
def get_genres(library_manager: CurrentLibrary):
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
@subsonic_router.get("/getMoods.view")
def get_moods(library_manager: CurrentLibrary):
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
def delete_user(
    library_manager: CurrentLibrary,
    username: str,
    user: Annotated[User, Depends(get_user)],
):
    check_subsonic_error(library_manager.delete_user_by_username(username, user.id))
    return {}


@subsonic_router.get("/download")
def download_to_user():
    return {"hello world"}


@subsonic_router.get("/startScan")
def start_scan(library_manager: CurrentLibrary):
    library_manager.sync(task_id="sub")
    return {
        "scanStatus": {"scanning": True, "count": 0},
    }


@subsonic_router.get("/getSimilarSongs2")
def getSimiliarSong(library_manager: CurrentLibrary, id: int, count: int = 50):
    tracks = check_subsonic_error(
        library_manager.get_similiar_artists_random_tracks(id, count)
    )
    return {"similarSongs2": {"song": [to_subsonic_song(track) for track in tracks]}}


@subsonic_router.get("/getScanStatus.view")
@subsonic_router.get("/getScanStatus")
def scan_status(library_manager: CurrentLibrary):
    task = check_subsonic_error(library_manager.get_sync_task("sub"))
    is_scanning = task.status == "processing"
    count = (
        task.result.covers.added
        + task.result.lyrics.added
        + task.result.tracks.added
        + task.result.videos.added
    )
    return {
        "scanStatus": {"scanning": is_scanning, "count": count},
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


class SubsonicApi(Interface):
    ID = "subsonic-api"

    async def start(self):
        port = int(self.config.get("port", 8000))
        host = self.config.get("host", "0.0.0.0")
        docs = self.config.get("docs", False)
        app = FastAPI(
            docs_url="/docs" if docs else None,
            redoc_url="/redoc" if docs else None,
            openapi_url="/openapi.json" if docs else None,
        )
        app.state.library_manager = self.library_manager
        app.state.SECRET_KEY = self.config.get("jwt_secret", "test-key")
        app.state.ALLOW_REGISTRATION = self.config.get("allow_registration", False)
        app.add_middleware(
            CORSMiddleware,
            allow_origin_regex=r".*",
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        app.add_exception_handler(SubsonicException, subsonic_exception_handler)
        app.middleware("http")(subsonic_middleware)
        app.include_router(subsonic_router)
        app.include_router(admin_router.auth_router)
        app.include_router(
            admin_router.router, dependencies=[Depends(admin_router.user_auth)]
        )
        config = uvicorn.Config(app, port=port, host=host)
        server = uvicorn.Server(config)
        await server.serve()
