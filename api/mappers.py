from core.schemas.schemas import (
    Artist,
    Album,
    Playlist,
    Track,
    LyricsResponse,
)


def to_subsonic_song(track: Track):
    song = {
        "id": track.id,
        "parent": track.album.id,
        "isDir": False,
        "title": track.title,
        "album": track.album.title,
        "artist": track.album.artist[0].name,
        "duration": int(track.length / 1000),
        "created": track.created_at,
        "albumId": track.album.id,
        "artistId": track.album.artist[0].id,
        "musicVideo": "cl-" + track.music_videos,
        "type": "music",
        "mediaType": "song",
        "isVideo": False,
    }
    if track.album.cover_path:
        song["coverArt"] = f"{track.album.cover_path}"
    return song


def to_subsonic_album(album: Album):
    artist = album.artist[0]
    sub_album = {
        "id": album.id,
        "parent": artist.id,
        "album": album.title,
        "title": album.title,
        "name": album.title,
        "isDir": True,
        "songCount": len(album.tracks),
        "created": album.created_at,
        "duration": int(album.duration / 1000),
        "artistId": artist.id,
        "artist": artist.name,
    }
    if album.cover_path:
        sub_album["coverArt"] = f"{album.cover_path}"
    return sub_album


def to_subsonic_artist(artist: Artist):
    sub_artist = {
        "id": artist.id,
        "name": artist.name,
        "albumCount": len(artist.albums),
    }
    if artist.cover_path:
        sub_artist["coverArt"] = f"{artist.cover_path}"
    return sub_artist


def to_subsonic_playlist(playlist: Playlist):
    sub_playlist = {
        "id": playlist.id,
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
    for line in lyrics.synced_text:
        sub_lyrics["line"].append({"start": line["time"], "value": line["text"]})
    return sub_lyrics


def external_track_to_subsonic(track: Track):
    song = {
        "id": track.external_id,
        "isDir": False,
        "title": track.title,
        "album": track.album,
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
        "artist": album.artists[0],
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
        "albumCount": len(artist["albums"]),
    }

    if artist.cover_path:
        sub_artist["coverArt"] = artist.cover_path

    if artist.id:
        sub_artist["db_id"] = artist.id

    return sub_artist
