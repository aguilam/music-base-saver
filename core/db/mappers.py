from core.db.models import (
    TrackORM,
    ArtistORM,
    AlbumORM,
    PlaylistORM,
    MusicVideoORM,
    LyricsORM,
    UserORM,
)
from core.schemas.schemas import (
    Track,
    Artist,
    Album,
    Playlist,
    MusicVideo,
    Lyrics,
    User,
)


def artist_from_orm(artist: ArtistORM) -> Artist:
    return Artist(
        id=artist.id,
        name=artist.name,
        cover_path=artist.cover_path,
        albums=[album_from_orm(album) for album in artist.albums],
    )


def album_from_orm(album: AlbumORM) -> Album:
    return Album(
        id=album.id,
        title=album.title,
        cover_path=album.cover_path,
        duration=album.duration,
        tracks_count=album.track_count,
        artist=artist_from_orm(album.artist_rel),
        tracks=[track_from_orm(track) for track in album.tracks],
        created_at=album.created_at,
    )


def playlist_from_orm(playlist: PlaylistORM) -> Playlist:
    return Playlist(
        id=playlist.id,
        title=playlist.title,
        cover_path=playlist.cover_path,
        is_public=playlist.is_public,
        owner=user_from_orm(playlist.owner),
        duration=playlist.duration,
        tracks_count=playlist.track_count,
        tracks=[track_from_orm(track) for track in playlist.tracks],
        created_at=playlist.created_at,
    )


def track_from_orm(track: TrackORM) -> Track:
    return Track(
        id=track.id,
        title=track.title,
        length=track.length,
        artists=[artist_from_orm(artist) for artist in track.artists],
        album=album_from_orm(track.album),
        album_position=track.album_position,
        cover_path=track.album.cover_path,
        path=next(link for link in track.links),
        bpm=track.bpm,
        track_gain=track.trackGain,
        track_peak=track.trackPeak,
        year=track.year,
        disc_number=track.discNumber,
        lyrics=[lyrics_from_orm(lyrics) for lyrics in track.lyrics],
        music_videos=[music_video_from_orm(video) for video in track.music_videos],
        created_at=track.created_at,
    )


def lyrics_from_orm(lyrics: LyricsORM) -> Lyrics:
    return Lyrics(
        id=lyrics.id,
        is_synced=lyrics.is_synced,
        synced_text=lyrics.synced_text,
        plain_text=lyrics.plain_text,
        language=lyrics.language,
        path=lyrics.original_path,
        type=lyrics.type,
        offset=lyrics.offset,
        track_id=lyrics.track_id,
    )


def music_video_from_orm(music_video: MusicVideoORM) -> MusicVideo:
    return MusicVideo(
        id=music_video.id,
        local_link=music_video.local_link,
        track_id=music_video.track_id,
    )


def user_from_orm(user: UserORM) -> User:
    return User(
        id=user.id,
        username=user.username,
        password=user.password,
        email=user.email,
        api_key=user.api_key,
        is_admin=user.is_admin,
    )
