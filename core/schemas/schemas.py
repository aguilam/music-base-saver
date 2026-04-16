from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class Artist:
    id: int | None
    name: str
    cover_path: str | None
    albums: list[Album]
    external_id: int | None = None


@dataclass(slots=True)
class ArtistShort:
    id: int | None
    name: str
    cover_path: str | None
    external_id: int | None = None


@dataclass(slots=True)
class Album:
    id: int | None
    title: str
    cover_path: str | None
    duration: int
    tracks_count: int
    artist: Artist
    tracks: list[Track]
    created_at: datetime
    external_id: int | None = None


@dataclass(slots=True)
class AlbumShort:
    id: int | None
    title: str
    cover_path: str | None
    duration: int
    tracks_count: int
    artist: ArtistShort
    tracks: list[Track]
    created_at: datetime
    external_id: int | None = None


@dataclass(slots=True)
class Playlist:
    id: int | None
    title: str
    cover_path: str | None
    tracks: list[Track]
    owner: User
    is_public: bool
    tracks_count: int
    duration: int
    created_at: datetime


@dataclass(slots=True)
class Track:
    id: int | None
    title: str
    artists: list[ArtistShort]
    album: Album | None
    cover_path: str | None
    path: str | None
    length: int
    album_position: int | None
    bpm: int | None
    track_gain: float | None
    track_peak: float | None
    disc_number: int | None
    year: int | None
    lyrics: list[Lyrics]
    music_videos: list[MusicVideo]
    created_at: datetime
    external_id: int | None = None


@dataclass(slots=True)
class TrackShort:
    id: int | None
    title: str
    cover_path: str | None
    path: str | None
    length: int
    album_position: int | None
    bpm: int | None
    track_gain: float | None
    track_peak: float | None
    disc_number: int | None
    year: int | None
    created_at: datetime
    external_id: int | None = None


@dataclass(slots=True)
class Lyrics:
    id: int | None
    is_synced: bool
    synced_text: dict | None
    plain_text: str | None
    language: str
    path: str
    type: str
    offset: int
    track_id: int | None


@dataclass(slots=True)
class LyricsResponse:
    id: int | None
    artist: str
    title: str
    is_synced: bool
    synced_text: dict | None
    plain_text: str | None
    language: str
    offset: int


@dataclass(slots=True)
class MusicVideo:
    id: int | None
    local_link: str
    track_id: int


@dataclass(slots=True)
class User:
    id: int | None
    username: str
    password: str
    email: str
    api_key: str | None
    is_admin: bool
