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
)

T = TypeVar("T")


def _required(value: T | None) -> T:
    if value is None:
        raise ValueError("Cannot build response, required attr not given")
    return value


def to_short_artist_response(artist: Artist | ArtistShort) -> ShortArtistResponse:
    return ShortArtistResponse(
        id=_required(artist.id),
        name=artist.name,
        cover_id=artist.cover_path,
        external_id=artist.external_id,
    )


def to_short_album_response(album: Album | AlbumShort) -> ShortAlbumResponse:
    return ShortAlbumResponse(
        id=_required(album.id),
        title=album.title,
        cover_id=album.cover_path,
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
        length=track.length,
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


def to_full_artist_response(artist: Artist) -> FullArtistResponse:
    return FullArtistResponse(
        id=_required(artist.id),
        name=artist.name,
        description=artist.description,
        cover_id=artist.cover_path,
        external_id=artist.external_id,
        genres=list(artist.genres),
        albums=[to_short_album_response(album) for album in artist.albums],
    )
