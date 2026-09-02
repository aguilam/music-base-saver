from core.responses import (
    FullArtistResponse,
    FullAlbumResponse,
    FullPlaylistResponse,
    FullTrackResponse,
    ShortAlbumResponse,
    ShortArtistResponse,
    ShortTrackResponse,
    ShortPlaylistResponse,
    LyricsResponse,
)


def to_subsonic_song(track: FullTrackResponse | ShortTrackResponse):
    primary_album = next((album for album in track.albums if album.is_primary), None)
    song = {
        "id": str(track.id),
        "parent": primary_album.id if primary_album else None,
        "isDir": False,
        "title": track.title,
        "album": primary_album.title if primary_album else None,
        "artist": ", ".join(artist.name for artist in track.artists),
        "duration": int(track.duration / 1000),
        "created": track.created_at,
        "albumId": str(primary_album.id) if primary_album else None,
        "artistId": str(primary_album.artists[0].id) if primary_album else None,
        "type": "music",
        "mediaType": "song",
        "isVideo": False,
    }
    if isinstance(track, FullTrackResponse):
        song["musicVideo"] = (
            f"cl-{track.music_videos[0].id}" if len(track.music_videos) > 0 else None
        )
    if primary_album and primary_album.cover_path:
        song["coverArt"] = f"{primary_album.cover_path}"
    return song


def to_subsonic_album(album: FullAlbumResponse | ShortAlbumResponse):
    artist = album.artists[0]
    sub_album = {
        "id": str(album.id),
        "parent": str(artist.id),
        "album": album.title,
        "title": album.title,
        "name": album.title,
        "isDir": True,
        "songCount": len(album.tracks),
        "created": album.created_at,
        "duration": int(album.duration / 1000) if album.duration else None,
        "artistId": str(artist.id),
        "artist": artist.name,
    }
    if album.cover_id:
        sub_album["coverArt"] = f"{album.cover_id}"
    return sub_album


def to_subsonic_artist(artist: FullArtistResponse | ShortArtistResponse):
    sub_artist = {
        "id": str(artist.id),
        "name": artist.name,
        "albumCount": len(artist.albums),
    }
    if artist.cover_id:
        sub_artist["coverArt"] = f"{artist.cover_id}"
    return sub_artist


def to_subsonic_playlist(playlist: FullPlaylistResponse | ShortPlaylistResponse):
    sub_playlist = {
        "id": str(playlist.id),
        "name": playlist.title,
        "owner": playlist.owners[0].username,
        "public": playlist.is_public,
        "created": playlist.created_at,
        "changed": playlist.created_at,
        "songCount": playlist.tracks_count,
        "duration": int(playlist.duration / 1000),
    }
    return sub_playlist


def to_subsonic_lyric(lyrics: LyricsResponse):
    sub_lyrics = {
        "displayArtist": lyrics.artist,
        "displayTitle": lyrics.title,
        "lang": lyrics.language,
        "offset": lyrics.offset,
        "synced": lyrics.is_synced,
        "line": [],
    }
    if lyrics.synced_text is not None:
        for line in lyrics.synced_text:
            sub_lyrics["line"].append({"start": line["time"], "value": line["text"]})
    elif lyrics.plain_text is not None:
        for line in lyrics.plain_text.split("\n"):
            sub_lyrics["line"].append({"value": line})
    return sub_lyrics


def external_track_to_subsonic(track: Track):
    song = {
        "id": track.external_id,
        "isDir": False,
        "title": track.title,
        "album": track.albums[0].title,
        "artist": (track.artists[0]),
        "duration": track.length,
        "type": "music",
        "mediaType": "song",
        "isVideo": False,
    }

    if track.cover_path:
        song["coverArt"] = track.cover_path

    if track.id:
        song["db_id"] = track.id

    return song


def external_album_to_subsonic(album: Album):
    sub_album = {
        "id": album.external_id,
        "album": album.title,
        "title": album.title,
        "name": album.title,
        "isDir": True,
        "artist": album.artists[0].name,
        "songCount": album.tracks_count,
        "created": album.created_at,
    }
    if album.cover_path:
        sub_album["coverArt"] = album.cover_path

    if album.id:
        sub_album["db_id"] = album.id
        # sub_album["parent"] = album.get("artist_id")
        # sub_album["artistId"] = album.get("artist_id")
    if album.tracks:
        if album.duration:
            sub_album["duration"] = album.duration
    return sub_album


def external_artist_to_subsonic(artist: Artist):
    sub_artist = {
        "id": artist.external_id,
        "name": artist.name,
        "albumCount": len(artist.albums),
    }

    if artist.cover_path:
        sub_artist["coverArt"] = artist.cover_path

    if artist.id:
        sub_artist["db_id"] = artist.id

    return sub_artist
