from __future__ import annotations

from typing import TypeVar

from core.schemas.schemas import (
    Album,
    AlbumShort,
    Artist,
    ArtistShort,
    FullAlbumResponse,
    FullArtistResponse,
    FullPlaylistResponse,
    Playlist,
    ShortAlbumResponse,
    ShortArtistResponse,
    ShortTrackResponse,
    ShortUserResponse,
    Track,
    TrackShort,
    User,
    FullTrackResponse,
    ShortLyricsResponse,
    ShortMusicVideoResponse,
    ShortLyricsResponse,
    Lyrics,
    MusicVideo,
)

T = TypeVar("T")


def _required(value: T | None) -> T:
    if value is None:
        raise ValueError("Cannot build response, required attr not given")
    return value


def to_short_artist_response(artist: Artist | ArtistShort) -> ShortArtistResponse:
    # TODO: Add albums count
    return ShortArtistResponse(
        id=_required(artist.id),
        name=artist.name,
        albums_count=0,
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
        external_id=album.external_id,
        artists=[to_short_artist_response(artist) for artist in album.artists],
    )


def to_short_user_response(user: User) -> ShortUserResponse:
    return ShortUserResponse(
        id=_required(user.id),
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
        tracks=[to_short_track_response(track) for track in album.tracks],
        artists=[to_short_artist_response(artist) for artist in album.artists],
        genres=list(album.genres),
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
        tracks=[to_short_track_response(track) for track in playlist.tracks],
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


def to_short_music_video_response(music_video: MusicVideo) -> ShortMusicVideoResponse:
    return ShortMusicVideoResponse(
        id=_required(music_video.id),
        track_id=music_video.track_id,
        duration=music_video.duration_ms,
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
        external_id=track.external_id,
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
        albums_count=0,
        description=artist.description,
        cover_id=artist.cover_path,
        external_id=artist.external_id,
        genres=list(artist.genres),
        created_at=_required(artist.created_at),
        albums=[to_short_album_response(album) for album in artist.albums],
    )
