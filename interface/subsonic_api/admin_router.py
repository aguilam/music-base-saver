from fastapi import APIRouter

router = APIRouter()


@router.post("/login")
def login():
    pass


@router.post("/logout")
def logout():
    pass


@router.get("/search")
def search():
    pass


@router.get("/users")
def get_users():
    pass


@router.post("/users")
def post_user():
    pass


@router.get("/users/{id}")
def get_user():
    pass


@router.delete("/users/{id}")
def delete_user():
    pass


@router.patch("/users/{id}")
def patch_user():
    pass


@router.get("/users/{id}/api-keys")
def get_api_keys():
    pass


@router.post("/users/{id}/api-keys")
def post_api_key():
    pass


@router.delete("/users/{id}/api-keys/{key_id}")
def revoke_api_key():
    pass


@router.get("/users/{id}/providers-keys")
def get_providers_keys():
    pass


@router.post("/users/{id}/providers-keys")
def post_providers_key():
    pass


@router.delete("/users/{id}/providers-keys/{key_id}")
def revoke_providers_key():
    pass


@router.get("/config")
def get_config():
    pass


@router.put("/config")
def put_config():
    pass


@router.get("/status")
def get_status():
    pass


@router.get("/artists")
def get_artists():
    pass


@router.get("/artists/:id")
def get_artist():
    pass


@router.get("/albums")
def get_albums():
    pass


@router.get("/albums/:id")
def get_album():
    pass


@router.get("/playlists")
def get_playlists():
    pass


@router.post("/playlists")
def post_playlist():
    pass


@router.get("/playlists/:id")
def get_playlist():
    pass


@router.delete("/playlists/:id")
def delete_playlist():
    pass


@router.patch("/playlists/:id")
def patch_playlist():
    pass


@router.post("/scans")
def post_scan():
    pass


@router.get("/scans")
def get_scans():
    pass


@router.get("/scans/{id}")
def get_scan():
    pass


@router.delete("/scans/{id}")
def cancel_scan():
    pass


@router.get("/logs")
def get_logs():
    pass


@router.get("/tracks")
def get_tracks():
    pass


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
