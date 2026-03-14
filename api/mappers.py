from core.db.models import Playlist, Album, Artist, Track


def to_subsonic_song(track: Track):
    return {
        "id": track.id,
        "parent": track.album_id,
        "isDir": False,
        "title": track.title,
        "album": track.album.title,
        "artist": track.album.artist_rel.name,
        "coverArt": track.album.cover_path,
        "duration": track.length,
        "created": track.created_at,
        "albumId": track.album_id,
        "artistId": track.album.artist_id,
        "type": "music",
        "mediaType": "song",
        "isVideo": False,
    }


def to_subsonic_album(album: Album):
    return {
        "id": album.id,
        "parent": album.artist_id,
        "album": album.title,
        "title": album.title,
        "name": album.title,
        "isDir": True,
        "coverArt": album.cover_path,
        "songCount": len(album.tracks),
        "created": album.created_at,
        "duration": album.duration,
        "artistId": album.artist_id,
        "artist": album.artist_rel.name,
    }


def to_subsonic_artist(artist: Artist):
    return {
        "id": artist.id,
        "name": artist.name,
        "coverArt": "test",
        "albumCount": len(artist.albums),
    }


def to_subsonic_playlist(playlist: Playlist):
    return {
        "id": playlist.id,
        "name": playlist.name,
        "owner": playlist.owner.username,
        "public": playlist.public,
        "created": playlist.created_at,
        "changed": playlist.created_at,
        "songCount": playlist.song_count,
        "duration": playlist.duration,
    }
