from core.db.models import Playlist, Album, Artist, Track


def to_subsonic_song(track: Track):
    song = {
        "id": track.id,
        "parent": track.album_id,
        "isDir": False,
        "title": track.title,
        "album": track.album.title,
        "artist": track.album.artist_rel.name,
        "duration": int(track.length / 1000),
        "created": track.created_at,
        "albumId": track.album_id,
        "artistId": track.album.artist_id,
        "musicVideo": "cl-" + track.music_videos,
        "type": "music",
        "mediaType": "song",
        "isVideo": False,
    }
    if track.album.cover_path:
        song["coverArt"] = f"al-{track.album.id}"
    return song


def to_subsonic_album(album: Album):
    sub_album = {
        "id": album.id,
        "parent": album.artist_id,
        "album": album.title,
        "title": album.title,
        "name": album.title,
        "isDir": True,
        "songCount": len(album.tracks),
        "created": album.created_at,
        "duration": int(album.duration / 1000),
        "artistId": album.artist_id,
        "artist": album.artist_rel.name,
    }
    if album.cover_path:
        sub_album["coverArt"] = f"al-{album.id}"
    return sub_album


def to_subsonic_artist(artist: Artist):
    sub_artist = {
        "id": artist.id,
        "name": artist.name,
        "albumCount": len(artist.albums),
    }
    if artist.cover_path:
        sub_artist["coverArt"] = f"ar-{artist.id}"
    return sub_artist


def to_subsonic_playlist(playlist: Playlist):
    sub_playlist = {
        "id": playlist.id,
        "name": playlist.name,
        "owner": playlist.owner.username,
        "public": playlist.public,
        "created": playlist.created_at,
        "changed": playlist.created_at,
        "songCount": playlist.song_count,
        "duration": int(playlist.durationint / 1000),
    }
    return sub_playlist


def to_subsonic_lyric(lyric: dict):
    sub_lyric = {
        "displayArtist": lyric["artist"],
        "displayTitle": lyric["title"],
        "lang": lyric["language"],
        "offset": lyric["offset"],
        "synced": lyric["synced"],
        "line": [],
    }
    for line in lyric["lines"]:
        sub_lyric["line"].append({"start": line["time"], "value": line["text"]})
    return sub_lyric


def external_track_to_subsonic(track: dict):
    song = {
        "id": track["id"],
        "isDir": False,
        "title": track["title"],
        "album": track["album"],
        "artist": (
            track["artist"][0] if isinstance(track["artist"], list) else track["artist"]
        ),
        "duration": track["length"],
        "type": "music",
        "mediaType": "song",
        "isVideo": False,
    }

    if track.get("cover_url"):
        song["coverArt"] = track["cover_url"]

    if track.get("db_id"):
        song["db_id"] = track["db_id"]
        song["parent"] = track.get("album_id")
        song["albumId"] = track.get("album_id")
        song["artistId"] = track.get("artist_id")

    return song


def external_album_to_subsonic(album: dict):
    sub_album = {
        "id": album["id"],
        "album": album["title"],
        "title": album["title"],
        "name": album["title"],
        "isDir": True,
        "artist": album["artist"],
    }
    if album.get("cover_url"):
        sub_album["coverArt"] = album["cover_url"]

    if album.get("db_id"):
        sub_album["db_id"] = album["db_id"]
        sub_album["parent"] = album.get("artist_id")
        sub_album["artistId"] = album.get("artist_id")
        if album.get("created_at"):
            sub_album["created"] = album["created_at"]
    if album.get("tracks"):
        sub_album["songCount"] = len(album["tracks"])
        if album.get("duration"):
            sub_album["duration"] = album["duration"]
    return sub_album


def external_artist_to_subsonic(artist: dict):
    sub_artist = {
        "id": artist["id"],
        "name": artist["name"],
    }

    if artist.get("cover_url"):
        sub_artist["coverArt"] = artist["cover_url"]

    if artist.get("db_id"):
        sub_artist["db_id"] = artist["db_id"]
    if artist.get("albums"):
        sub_artist["albumCount"] = len(artist["albums"])

    return sub_artist
