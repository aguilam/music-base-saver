from models import TrackORM, ArtistORM, AlbumORM, PlaylistORM, MusicVideoORM, LyricsORM
from schemas.schemas import Track, Artist, Album, Playlist, MusicVideo, Lyrics


def artist_from_orm(db_artist: ArtistORM) -> Artist:
    return Artist(
        id=db_artist.id,
        name=db_artist.name,
        cover_path=db_artist.cover_path,
    )


def album_from_orm(db_album: AlbumORM) -> Album:
    return Album(
        id=db_album.id,
        title=db_album.title,
        cover_path=db_album.cover_path,
        duration=db_album.duration,
        tracks_count=db_album.track_count,
        artist=artist_from_orm(db_album.artist_rel),
        tracks=[track_from_orm(track) for track in db_album.tracks],
    )


def playlist_from_orm(db_playlist: PlaylistORM) -> Playlist:
    return Playlist(
        id=db_playlist.id,
        title=db_playlist.title,
        cover_path=db_playlist.cover_path,
        is_public=db_playlist.public,
        duration=db_playlist.duration,
        tracks_count=db_playlist.track_count,
        tracks=[track_from_orm(track) for track in db_playlist.tracks],
    )


def track_from_orm(db_track: TrackORM) -> Track:
    return Track(
        id=db_track.id,
        title=db_track.title,
        length=db_track.length,
        artists_id=[artist.id for artist in db_track.artists],
        artists_names=[artist.name for artist in db_track.artists],
        album_id=db_track.album_id,
        album_name=db_track.album.title,
        album_position=db_track.album_position,
        cover_path=db_track.album.cover_path,
        path=next(link for link in db_track.links),
        bpm=db_track.bpm,
        track_gain=db_track.trackGain,
        track_peak=db_track.trackPeak,
        year=db_track.year,
        disc_number=db_track.discNumber,
    )


def lyrics_from_orm(db_lyrics: LyricsORM) -> Lyrics:
    return Lyrics(
        id=db_lyrics.id,
        is_synced=db_lyrics.is_synced,
        synced_text=db_lyrics.synced_text,
        plain_text=db_lyrics.plain_text,
        language=db_lyrics.language,
        path=db_lyrics.original_path,
        type=db_lyrics.type,
        offset=db_lyrics.offset,
        track_id=db_lyrics.track_id,
    )


def music_video_from_orm(db_video: MusicVideoORM) -> MusicVideo:
    return MusicVideo(
        id=db_video.id, local_link=db_video.local_link, track_id=db_video.track_id
    )
