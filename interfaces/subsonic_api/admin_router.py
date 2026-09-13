import time
from dataclasses import asdict, fields
from typing import Annotated
from urllib.parse import quote

import jwt
from fastapi import APIRouter, Body, Depends, HTTPException, Request, Response, status
from fastapi.responses import StreamingResponse

from interfaces.subsonic_api.utils import CurrentLibrary, check_result, to_camel


def create_keys(SECRET_KEY: str, id: int, is_admin: bool) -> tuple[str, str]:
    now = int(time.time())
    access_token = jwt.encode(
        {
            "sub": str(id),
            "role": "admin" if is_admin else "user",
            "exp": now + 60 * 15,
            "iat": now,
        },
        SECRET_KEY,
        algorithm="HS256",
    )
    refresh_token = jwt.encode(
        {
            "sub": str(id),
            "role": "admin" if is_admin else "user",
            "exp": now + 60 * 60 * 24 * 14,
            "type": "refresh",
            "iat": now,
        },
        SECRET_KEY,
        algorithm="HS256",
    )
    return (access_token, refresh_token)


def set_cookie(response: Response, request: Request, id: int, is_admin: bool):
    SECRET_KEY = request.app.state.SECRET_KEY
    access_token, refresh_token = create_keys(SECRET_KEY, id, is_admin)
    response.set_cookie(
        "access_token",
        access_token,
        httponly=True,
    )
    response.set_cookie(
        "refresh_token",
        refresh_token,
        httponly=True,
        path="/api/auth/refresh",
    )


def user_auth(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    try:
        SECRET_KEY = request.app.state.SECRET_KEY
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


router = APIRouter(tags=["Admin API"])
auth_router = APIRouter(prefix="/auth", tags=["Admin API"])


@auth_router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    library: CurrentLibrary,
    request: Request,
    response: Response,
    username: str = Body(),
    password: str = Body(),
):
    if not request.app.state.ALLOW_REGISTRATION:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Registration is disabled on this server",
        )
    user = check_result(library.create_user(username, "", password))
    set_cookie(response, request, user.id, user.is_admin)


@auth_router.post("/login")
def login(
    library: CurrentLibrary,
    response: Response,
    request: Request,
    username: str = Body(),
    password: str = Body(),
):
    user = check_result(library.check_user_login(username=username, password=password))
    set_cookie(response, request, user.id, user.is_admin)


@auth_router.post("/refresh")
def refresh(request: Request, response: Response):
    token = request.cookies.get("refresh_token")
    SECRET_KEY = request.app.state.SECRET_KEY
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    if payload.get("type", None) != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    now = int(time.time())
    payload["iat"] = now
    payload["exp"] = now + 60 * 15
    payload.pop("type", None)
    access_token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    response.set_cookie("access_token", access_token, httponly=True)


@auth_router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token", path="/api/auth/refresh")


@auth_router.get("/me")
def get_me(library: CurrentLibrary, request: Request):
    token = request.cookies.get("access_token")
    SECRET_KEY = request.app.state.SECRET_KEY
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    user = check_result(library.get_user(user_id=int(user_id)))
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return {
        "id": user.id,
        "username": user.username,
        "isAdmin": user.is_admin,
    }


@router.get("/search/library")
def global_search(
    library: CurrentLibrary,
    query: str,
    artist_offset: int = 0,
    album_offset: int = 0,
    track_offset: int = 0,
):
    searched = library.local_search(
        query=query,
        artistCount=10,
        albumCount=10,
        songCount=10,
        artistOffset=artist_offset,
        albumOffset=album_offset,
        songOffset=track_offset,
    )
    return to_camel(asdict(searched))


@router.get("/search/external")
def local_search(library: CurrentLibrary, query: str):
    searched = library.global_search(query=query)
    return to_camel(asdict(searched))


@router.get("/users")
def get_users(library: CurrentLibrary, user: Annotated[dict, Depends(user_auth)]):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not permitted")
    users = library.get_all_users()
    return [to_camel(asdict(user)) for user in users]


@router.post("/users")
def post_user(
    library: CurrentLibrary,
    user: Annotated[dict, Depends(user_auth)],
    username: str = Body(),
    password: str = Body(),
):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not permitted")
    new_user = check_result(library.create_user(username, "", password))
    return to_camel(asdict(new_user))


@router.get("/users/{id}")
def get_user(id: int, library: CurrentLibrary):
    user = check_result(library.get_user(user_id=id))
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return {"id": user.id, "username": user.username}


@router.delete("/users/{id}")
def delete_user(
    id: int, library: CurrentLibrary, user: Annotated[dict, Depends(user_auth)]
):
    check_result(library.delete_user_by_id(id, int(user["sub"])))


@router.patch("/users/{id}")
def patch_user(
    library: CurrentLibrary,
    acting_user: Annotated[dict, Depends(user_auth)],
    id: int,
    username: str | None = Body(default=None),
    password: str | None = Body(default=None),
    is_admin: bool | None = Body(default=None),
):
    new_user = check_result(
        library.update_user_by_id(
            acting_user_id=int(acting_user["sub"]),
            changed_user_id=id,
            new_username=username,
            new_password=password,
            set_is_admin=is_admin,
        )
    )
    return to_camel(asdict(new_user))


@router.get("/user/{id}/playlists")
def get_user_playlists(library: CurrentLibrary, id: int):
    playlists = library.get_user_playlists(id)
    return [to_camel(asdict(playlist)) for playlist in playlists]


@router.get("/api-keys")
def get_api_keys(library: CurrentLibrary, user: Annotated[dict, Depends(user_auth)]):
    api_keys = library.get_user_api_keys(user["sub"])
    return [to_camel(asdict(key)) for key in api_keys]


@router.post("/api-keys")
def post_api_key(library: CurrentLibrary, user: Annotated[dict, Depends(user_auth)]):
    api_key = check_result(library.create_api_key(user_id=user["sub"]))
    return to_camel(asdict(api_key))


@router.delete("/api-keys/{key_id}")
def revoke_api_key(
    library: CurrentLibrary, user: Annotated[dict, Depends(user_auth)], key_id: int
):
    library.revoke_api_key(key_id)


@router.get("/providers")
def get_providers(library: CurrentLibrary):
    providers = library.get_provider_types()
    return providers


@router.get("/providers-keys")
def get_providers_keys(
    library: CurrentLibrary, user: Annotated[dict, Depends(user_auth)]
):
    api_keys = library.get_user_provider_keys(user["sub"])
    return [to_camel(asdict(key)) for key in api_keys]


@router.post("/providers-keys")
def post_providers_key(
    library: CurrentLibrary,
    user: Annotated[dict, Depends(user_auth)],
    key: str = Body(),
    provider: str = Body(),
):
    provider_key = check_result(
        library.create_provider_key(user_id=user["sub"], key=key, provider=provider)
    )
    return to_camel(asdict(provider_key))


@router.delete("/providers-keys/{key_id}")
def delete_provider_key(
    library: CurrentLibrary, user: Annotated[dict, Depends(user_auth)], key_id: int
):
    library.delete_provider_key(key_id)


@router.patch("/providers-keys/{key_id}")
def patch_provider_key(
    library: CurrentLibrary,
    user: Annotated[dict, Depends(user_auth)],
    key_id: int,
    key: str = Body(),
):
    library.change_provider_key(user_id=user["sub"], key_id=key_id, new_key=key)


@router.get("/config")
def get_config(
    library: CurrentLibrary,
    user: Annotated[dict, Depends(user_auth)],
):
    if user["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    return Response(content=library.get_config(), media_type="text/plain")


@router.put("/config")
async def put_config(
    request: Request,
    library: CurrentLibrary,
    user: Annotated[dict, Depends(user_auth)],
):
    if user["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    body_bytes = await request.body()
    config_str = body_bytes.decode("utf-8")
    library.change_config(config_str)


@router.get("/status")
def get_status(library: CurrentLibrary):
    status = library.check_status()
    return to_camel(asdict(status))


@router.get("/artists")
def get_artists(library: CurrentLibrary, cursor: str | None = None):
    items, new_cursor = library.get_artists_cursor(cursor)
    return {
        "items": [to_camel(asdict(artist)) for artist in items],
        "nextCursor": new_cursor,
        "hasMore": new_cursor is not None,
    }


@router.get("/artists/{id}")
def get_artist(library: CurrentLibrary, id: int):
    artist = check_result(library.get_artist_by_id(id))
    return to_camel(asdict(artist))


@router.get("/albums")
def get_albums(library: CurrentLibrary, cursor: str | None = None):
    items, new_cursor = library.get_albums_cursor(cursor)
    return {
        "items": [to_camel(asdict(album)) for album in items],
        "nextCursor": new_cursor,
        "hasMore": new_cursor is not None,
    }


@router.get("/albums/{id}")
def get_album(library: CurrentLibrary, id: int):
    album = check_result(library.get_album_by_id(id))
    return to_camel(asdict(album))


@router.get("/playlists")
def get_playlists(library: CurrentLibrary):
    pass


@router.post("/playlists")
def post_playlist(
    library: CurrentLibrary,
    user: Annotated[dict, Depends(user_auth)],
    title: str = Body(),
    track_ids: list[int] = Body(),
    is_public: bool = Body(),
):
    playlist = check_result(
        library.create_playlist(
            user_id=user["sub"], title=title, tracks_id=track_ids, is_public=is_public
        )
    )
    return to_camel(asdict(playlist))


@router.get("/playlists/{id}")
def get_playlist(library: CurrentLibrary, id: int):
    playlist = check_result(library.get_playlist_by_id(id))
    return to_camel(asdict(playlist))


@router.delete("/playlists/{id}")
def delete_playlist(
    library: CurrentLibrary, user: Annotated[dict, Depends(user_auth)], id: int
):
    check_result(library.delete_playlist(id))


@router.patch("/playlists/{id}")
def patch_playlist(
    library: CurrentLibrary,
    user: Annotated[dict, Depends(user_auth)],
    id: int,
    title: str | None = Body(default=None),
    track_ids: list[int] | None = Body(default=None),
    owner_ids: list[int] | None = Body(default=None),
    is_public: bool | None = Body(default=None),
):
    check_result(
        library.update_playlist(
            playlist_id=id,
            user_id=int(user["sub"]),
            title=title,
            track_ids=track_ids,
            owner_ids=owner_ids,
            is_public=is_public,
        )
    )


@router.post("/syncs", status_code=status.HTTP_201_CREATED)
def post_sync(library: CurrentLibrary, user: Annotated[dict, Depends(user_auth)]):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not permitted")
    sync_id = check_result(library.sync())
    return {"syncId": sync_id}


@router.get("/syncs")
def get_syncs(library: CurrentLibrary, user: Annotated[dict, Depends(user_auth)]):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not permitted")
    result = []
    for task_id, sync in library.get_sync_tasks().items():
        data = {
            field.name: getattr(sync, field.name)
            for field in fields(sync)
            if field.name != "task"
        }
        result.append({"id": task_id} | to_camel(data))
    return result


@router.get("/syncs/{id}")
def get_sync(
    library: CurrentLibrary, id: str, user: Annotated[dict, Depends(user_auth)]
):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not permitted")
    sync = check_result(library.get_sync_task(id))
    cameled = to_camel(asdict(sync))
    cameled.pop("task", None)
    return {"id": id} | cameled


@router.delete("/syncs/{id}")
def cancel_sync(
    library: CurrentLibrary, id: str, user: Annotated[dict, Depends(user_auth)]
):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not permitted")
    is_canceled = check_result(library.cancel_sync_task(id))
    return {"isCanceled": is_canceled}


@router.get("/logs")
def get_logs():
    pass


@router.get("/tracks")
def get_tracks(library: CurrentLibrary, cursor: str | None = None):
    items, new_cursor = library.get_tracks_cursor(cursor)
    return {
        "items": [to_camel(asdict(track)) for track in items],
        "nextCursor": new_cursor,
        "hasMore": new_cursor is not None,
    }


@router.post("/tracks")
def post_track():
    pass


@router.get("/tracks/{id}")
def get_track(library: CurrentLibrary, id: int):
    track = check_result(library.get_track_by_id(id))
    return to_camel(asdict(track))


@router.get("/tools/tracks")
def get_track_tools(library: CurrentLibrary):
    tools = check_result(library.get_track_tools())
    return [to_camel(asdict(tool)) for tool in tools]


@router.post("/tools/{tool_id}/tracks/{track_id}")
def post_track_tool_req(library: CurrentLibrary, track_id: int, tool_id: str):
    check_result(library.process_track(tool_func_id=tool_id, track_id=track_id))


@router.patch("/tracks/{id}")
def patch_track():
    pass


@router.get("/tracks/{id}/download")
def download_track(library: CurrentLibrary, id: str, request: Request):
    metadata = check_result(library.get_file_metadata(id))
    range_header = request.headers.get("range")
    content_disposition = (
        f'attachment; filename="download{metadata.file_suffix}"; '
        f"filename*=UTF-8''{quote(metadata.filename + metadata.file_suffix, safe='')}"
    )
    if not range_header:
        start = 0
        end = metadata.file_size - 1
        response_status = status.HTTP_200_OK
        headers = {
            "Content-Length": str(metadata.file_size),
            "Accept-Ranges": "bytes",
            "Content-Disposition": content_disposition,
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
            "Content-Disposition": content_disposition,
        }
    return StreamingResponse(
        check_result(library.stream_track(id, start, end)),
        headers=headers,
        status_code=response_status,
        media_type="application/octet-stream",
    )


@router.get("/tracks/{id}/lyrics")
def get_track_lyrics():
    pass


@router.post("/tracks/{id}/lyrics")
def post_track_lyrics():
    pass


@router.get("/tracks/{id}/music-video")
def get_track_music_video():
    pass


@router.post("/tracks/{id}/music-video")
def post_track_music_video():
    pass


@router.get("/stats")
def get_server_stats(library: CurrentLibrary):
    stats = library.get_library_stats()
    return to_camel(asdict(stats))


@router.post("/downloads", status_code=status.HTTP_201_CREATED)
def post_download(
    library: CurrentLibrary, object_id: str | None = Body(), query: str | None = Body()
):
    download_id = library.download(object_id=object_id, query=query)
    return {"downloadId": download_id}


@router.get("/downloads")
def get_downloads(library: CurrentLibrary):
    result = []
    for task_id, download in library.get_download_tasks().items():
        data = asdict(download)
        data.pop("task", None)
        result.append({"id": task_id} | to_camel(data))
    return result


@router.get("/downloads/{id}")
def get_download(library: CurrentLibrary, id: str):
    sync = check_result(library.get_download_task(id))
    cameled = to_camel(asdict(sync))
    cameled.pop("task", None)
    return {"id": id} | cameled


@router.delete("/downloads/{id}")
def cancel_downloads(library: CurrentLibrary, id: str):
    is_canceled = check_result(library.cancel_download_task(id))
    return {"isCanceled": is_canceled}


@router.get("/covers/{id}")
def get_cover(library: CurrentLibrary, id: int):
    cover_art = check_result(library.get_cover_art(id))
    return Response(content=cover_art.content, media_type=cover_art.mime)
