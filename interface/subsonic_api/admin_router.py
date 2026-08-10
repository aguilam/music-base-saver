from datetime import datetime
from typing import Annotated
import time
from fastapi import APIRouter, Request, Body, HTTPException, status, Response, Depends
import jwt
from interface.subsonic_api.utils import CurrentLibrary, to_camel
from dataclasses import asdict

SECRET_KEY = "4a1d7f8e3b2c9a1058f321d4c7a9b8e210459f8a3c2b1d0e9f8a7b6c5d4e3f2a"


def create_keys(id: int, is_admin: bool) -> tuple[str, str]:
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


def set_cookie(response: Response, id: int, is_admin: bool):
    access_token, refresh_token = create_keys(id, is_admin)
    response.set_cookie(
        "access_token",
        access_token,
        httponly=True,
    )
    response.set_cookie(
        "refresh_token",
        refresh_token,
        httponly=True,
        path="/auth/refresh",
    )


def user_auth(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


router = APIRouter()
auth_router = APIRouter(prefix="/auth")


@auth_router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    library: CurrentLibrary,
    response: Response,
    username: str = Body(),
    password: str = Body(),
):
    user = library.create_user(username, "", password)
    if user.id is None:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR)
    set_cookie(response, user.id, user.is_admin)


@auth_router.post("/login")
def login(
    library: CurrentLibrary,
    response: Response,
    username: str = Body(),
    password: str = Body(),
):
    user = library.get_user(username=username)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    if user.password != password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    set_cookie(response, user.id, user.is_admin)


@auth_router.post("/refresh")
def refresh(request: Request, response: Response):
    token = request.cookies.get("refresh_token")
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
    response.delete_cookie("refresh_token", path="/auth/refresh")


@auth_router.get("/me")
def get_me(library: CurrentLibrary, request: Request):
    token = request.cookies.get("access_token")
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
    user = library.get_user(user_id=int(user_id))
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return {
        "id": user.id,
        "username": user.username,
        "role": "admin" if user.is_admin else "user",
    }


@router.get("/search")
def search():
    pass


@router.get("/users")
def get_users(library: CurrentLibrary):
    users = library.get_all_users()
    return [to_camel(asdict(user)) for user in users]


@router.post("/users")
def post_user():
    pass


@router.get("/users/{id}")
def get_user(id: int, library: CurrentLibrary):
    user = library.get_user(user_id=id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return {"id": user.id, "username": user.username}


@router.delete("/users/{id}")
def delete_user(
    id: int, library: CurrentLibrary, user: Annotated[dict, Depends(user_auth)]
):
    deleted = library.delete_user_by_id(id, int(user["sub"]))
    if deleted is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


@router.patch("/users/{id}")
def patch_user(
    library: CurrentLibrary,
    user: Annotated[dict, Depends(user_auth)],
    id: int,
    username: str | None = None,
    password: str | None = None,
    is_admin: bool | None = None,
):
    new_user = library.update_user(
        user_id=id, username=username, password=password, is_admin=is_admin
    )
    return to_camel(asdict(new_user))


@router.get("/api-keys")
def get_api_keys(library: CurrentLibrary, user: Annotated[dict, Depends(user_auth)]):
    api_keys = library.get_user_api_keys(user["sub"])
    return [to_camel(asdict(key)) for key in api_keys]


@router.post("/api-keys")
def post_api_key(library: CurrentLibrary, user: Annotated[dict, Depends(user_auth)]):
    api_key = library.create_api_key(user_id=user["sub"])
    if api_key is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
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
    provider_key = library.create_provider_key(
        user_id=user["sub"], key=key, provider=provider
    )
    if provider_key is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
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
def get_artists(
    library: CurrentLibrary, id: int | None = None, created_at: str | None = None
):
    dt = None
    if created_at is not None:
        dt = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%S.%f")
    return [to_camel(asdict(artist)) for artist in library.get_artists_cursor(id, dt)]


@router.get("/artists/{id}")
def get_artist(library: CurrentLibrary, id: int):
    artist = library.get_artist_by_id(id)
    if artist is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return to_camel(asdict(artist))


@router.get("/albums")
def get_albums(
    library: CurrentLibrary, id: int | None = None, created_at: str | None = None
):
    dt = None
    if created_at is not None:
        dt = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%S.%f")
    return [to_camel(asdict(album)) for album in library.get_albums_cursor(id, dt)]


@router.get("/albums/{id}")
def get_album(library: CurrentLibrary, id: int):
    album = library.get_album_by_id(id)
    if album is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return to_camel(asdict(album))


@router.get("/playlists")
def get_playlists():
    pass


@router.post("/playlists")
def post_playlist():
    pass


@router.get("/playlists/{id}")
def get_playlist(library: CurrentLibrary, id: int):
    playlist = library.get_playlist_by_id(id)
    if playlist is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return to_camel(asdict(playlist))


@router.delete("/playlists/{id}")
def delete_playlist(
    library: CurrentLibrary, user: Annotated[dict, Depends(user_auth)], id: int
):
    pass


@router.patch("/playlists/{id}")
def patch_playlist():
    pass


@router.post("/syncs")
def post_scan(library: CurrentLibrary):
    id = library.sync()
    return {"syncId": id}


@router.get("/syncs")
def get_scans():
    pass


@router.get("/syncs/{id}")
def get_scan():
    pass


@router.delete("/syncs/{id}")
def cancel_scan():
    pass


@router.get("/logs")
def get_logs():
    pass


@router.get("/tracks")
def get_tracks(
    library: CurrentLibrary, id: int | None = None, created_at: str | None = None
):
    dt = None
    if created_at is not None:
        dt = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%S.%f")
    return [to_camel(asdict(track)) for track in library.get_tracks_cursor(id, dt)]


@router.post("/tracks")
def post_track():
    pass


@router.get("/tracks/{id}")
def get_track():
    pass


@router.patch("/tracks/{id}")
def patch_track():
    pass


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
