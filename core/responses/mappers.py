from __future__ import annotations

from core.responses import (
    FullArtistResponse,
    FullPlaylistResponse,
    FullAlbumResponse,
    FullTrackResponse,
    ShortAlbumResponse,
    ShortArtistResponse,
    ShortTrackResponse,
    ShortUserResponse,
    ShortLyricsResponse,
    ShortMusicVideoResponse,
    ShortPlaylistResponse,
    PlaylistTrackResponse,
    AlbumTrackResponse,
    TrackAlbumResponse,
    ShortGenreResponse,
    ShortMoodResponse,
)
from core.schemas import (
    Album,
    AlbumShort,
    Artist,
    ArtistShort,
    Playlist,
    Track,
    TrackShort,
    User,
    Lyrics,
    MusicVideo,
    StoredUser,
    PlaylistTrack,
    AlbumTrack,
    TrackAlbum,
    GenreShort,
    MoodShort,
)


def _required[T](value: T | None) -> T:
    if value is None:
        raise ValueError("Cannot build response, required attr not given")
    return value


def to_short_artist_response(artist: Artist | ArtistShort) -> ShortArtistResponse:
    return ShortArtistResponse(
        id=_required(artist.id),
        name=artist.name,
        albums_count=artist.albums_count if artist.albums_count else 0,
        cover_id=artist.cover_path,
        created_at=_required(artist.created_at),
        external_id=artist.external_id,
    )


def to_short_album_response(album: Album | AlbumShort) -> ShortAlbumResponse:
    return ShortAlbumResponse(
        id=_required(album.id),
        title=album.title,
        cover_id=album.cover_path,
        created_at=_required(album.created_at),
        duration=_required(album.duration),
        tracks_count=_required(album.tracks_count),
        album_type=album.album_type,
        external_id=album.external_id,
        genres=[to_short_genre_response(genre) for genre in album.genres],
        artists=[to_short_artist_response(artist) for artist in album.artists],
    )


def to_short_user_response(user: User | StoredUser) -> ShortUserResponse:
    return ShortUserResponse(
        id=_required(user.id),
        is_admin=user.is_admin,
        username=user.username,
    )


def to_short_track_response(track: Track | TrackShort) -> ShortTrackResponse:
    return ShortTrackResponse(
        id=_required(track.id),
        title=track.title,
        duration=track.length,
        created_at=_required(track.created_at),
        cover_id=track.cover_path,
        bpm=track.bpm,
        primary_album=to_track_album_response(track.primary_album)
        if track.primary_album
        else None,
        track_gain=track.track_gain,
        track_peak=track.track_peak,
        year=track.year,
        external_id=track.external_id,
        artists=[to_short_artist_response(artist) for artist in track.artists],
    )


def to_album_track_response(track: AlbumTrack) -> AlbumTrackResponse:
    return AlbumTrackResponse(
        id=_required(track.id),
        title=track.title,
        duration=track.length,
        created_at=_required(track.created_at),
        cover_id=track.cover_path,
        bpm=track.bpm,
        position=track.position,
        disc_number=track.disc_number,
        track_gain=track.track_gain,
        track_peak=track.track_peak,
        year=track.year,
        external_id=track.external_id,
        artists=[to_short_artist_response(artist) for artist in track.artists],
    )


def to_full_album_response(album: Album) -> FullAlbumResponse:
    return FullAlbumResponse(
        id=_required(album.id),
        title=album.title,
        duration=album.duration or 0,
        album_type=album.album_type,
        tracks_count=(
            album.tracks_count if album.tracks_count is not None else len(album.tracks)
        ),
        created_at=_required(album.created_at),
        year=album.year,
        description=album.description,
        cover_id=album.cover_path,
        external_id=album.external_id,
        genres=[to_short_genre_response(genre) for genre in album.genres],
        tracks=[to_album_track_response(track) for track in album.tracks],
        artists=[to_short_artist_response(artist) for artist in album.artists],
    )


def to_playlist_track_response(track: PlaylistTrack) -> PlaylistTrackResponse:
    return PlaylistTrackResponse(
        id=_required(track.id),
        title=track.title,
        duration=track.length,
        created_at=_required(track.created_at),
        cover_id=track.cover_path,
        bpm=track.bpm,
        position=track.position,
        primary_album=to_track_album_response(track.primary_album)
        if track.primary_album
        else None,
        track_gain=track.track_gain,
        track_peak=track.track_peak,
        year=track.year,
        external_id=track.external_id,
        artists=[to_short_artist_response(artist) for artist in track.artists],
    )


def to_full_playlist_response(playlist: Playlist) -> FullPlaylistResponse:
    return FullPlaylistResponse(
        id=_required(playlist.id),
        title=playlist.title,
        is_public=playlist.is_public,
        owners=[to_short_user_response(owner) for owner in playlist.owners],
        tracks_count=playlist.tracks_count,
        duration=playlist.duration,
        created_at=_required(playlist.created_at),
        tracks=[to_playlist_track_response(track) for track in playlist.tracks],
        cover_id=playlist.cover_path,
    )


def to_short_playlist_response(playlist: Playlist) -> ShortPlaylistResponse:
    return ShortPlaylistResponse(
        id=_required(playlist.id),
        title=playlist.title,
        is_public=playlist.is_public,
        owners=[to_short_user_response(owner) for owner in playlist.owners],
        tracks_count=playlist.tracks_count,
        duration=playlist.duration,
        created_at=_required(playlist.created_at),
        cover_id=playlist.cover_path,
    )


def to_short_lyrics_response(lyrics: Lyrics) -> ShortLyricsResponse:
    return ShortLyricsResponse(
        id=_required(lyrics.id),
        language=lyrics.language,
        track_id=_required(lyrics.track_id),
        offset=lyrics.offset,
        is_synced=lyrics.is_synced,
        synced_text=lyrics.synced_text,
        plain_text=lyrics.plain_text,
    )


def to_short_genre_response(genre: GenreShort) -> ShortGenreResponse:
    return ShortGenreResponse(id=_required(genre.id), name=genre.name)


def to_short_mood_response(genre: MoodShort) -> ShortMoodResponse:
    return ShortMoodResponse(id=_required(genre.id), name=genre.name)


def to_short_music_video_response(music_video: MusicVideo) -> ShortMusicVideoResponse:
    return ShortMusicVideoResponse(
        id=_required(music_video.id),
        track_id=music_video.track_id,
        duration=music_video.duration_ms,
    )


def to_track_album_response(album: TrackAlbum) -> TrackAlbumResponse:
    return TrackAlbumResponse(
        id=_required(album.id),
        title=album.title,
        duration=_required(album.duration),
        tracks_count=_required(album.tracks_count),
        created_at=_required(album.created_at),
        cover_id=album.cover_path,
        position=album.album_position,
        disc_number=album.disc_number,
        external_id=album.external_id,
        artists=[to_short_artist_response(artist) for artist in album.artists],
    )


def to_full_track_response(track: Track) -> FullTrackResponse:
    return FullTrackResponse(
        id=_required(track.id),
        title=track.title,
        duration=track.length,
        created_at=_required(track.created_at),
        cover_id=track.cover_path,
        bpm=track.bpm,
        track_gain=track.track_gain,
        track_peak=track.track_peak,
        year=track.year,
        primary_album=to_track_album_response(track.primary_album)
        if track.primary_album
        else None,
        albums=[to_track_album_response(album) for album in track.albums],
        external_id=track.external_id,
        genres=[to_short_genre_response(genre) for genre in track.genres],
        moods=[to_short_mood_response(moods) for moods in track.moods],
        artists=[to_short_artist_response(artist) for artist in track.artists],
        lyrics=[to_short_lyrics_response(lyrics) for lyrics in track.lyrics],
        music_videos=[
            to_short_music_video_response(music_video)
            for music_video in track.music_videos
        ],
    )


def to_full_artist_response(artist: Artist) -> FullArtistResponse:
    return FullArtistResponse(
        id=_required(artist.id),
        name=artist.name,
        albums_count=artist.albums_count if artist.albums_count else 0,
        description=artist.description,
        cover_id=artist.cover_path,
        external_id=artist.external_id,
        created_at=_required(artist.created_at),
        genres=[to_short_genre_response(genre) for genre in artist.genres],
        albums=[to_short_album_response(album) for album in artist.albums],
    )
