from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class Artist:
    id: int | None = None
    name: str
    cover_path: str | None = None
    albums: list[Album]
    external_id: int | None = None


@dataclass(slots=True)
class ArtistShort:
    id: int | None = None
    name: str
    cover_path: str | None = None
    external_id: int | None = None


@dataclass(slots=True)
class Album:
    id: int | None = None
    title: str
    cover_path: str | None = None
    duration: int
    tracks_count: int
    artist: Artist
    tracks: list[Track]
    created_at: datetime | None = None
    external_id: int | None = None


@dataclass(slots=True)
class AlbumShort:
    id: int | None = None
    title: str
    cover_path: str | None = None
    duration: int
    tracks_count: int
    artist: ArtistShort
    tracks: list[Track]
    created_at: datetime | None = None
    external_id: int | None = None


@dataclass(slots=True)
class Playlist:
    id: int | None = None
    title: str
    cover_path: str | None = None
    tracks: list[Track]
    owner: User
    is_public: bool = False
    tracks_count: int
    duration: int
    created_at: datetime | None = None


@dataclass(slots=True)
class Track:
    id: int | None = None
    title: str
    artists: list[ArtistShort]
    album: Album | None = None
    cover_path: str | None = None
    path: str | None = None
    length: int
    album_position: int | None = None
    bpm: int | None = None
    track_gain: float | None = None
    track_peak: float | None = None
    disc_number: int | None = None
    year: int | None = None
    lyrics: list[Lyrics]
    music_videos: list[MusicVideo]
    created_at: datetime | None = None
    external_id: int | None = None


@dataclass(slots=True)
class TrackShort:
    id: int | None = None
    title: str
    cover_path: str | None = None
    path: str | None = None
    length: int
    album_position: int | None = None
    bpm: int | None = None
    track_gain: float | None = None
    track_peak: float | None = None
    disc_number: int | None = None
    year: int | None = None
    created_at: datetime | None = None
    external_id: int | None = None


@dataclass(slots=True)
class Lyrics:
    id: int | None = None
    is_synced: bool = False
    synced_text: dict | None = None
    plain_text: str | None = None
    language: str
    path: str
    type: str
    offset: int = 0
    track_id: int | None = None


@dataclass(slots=True)
class LyricsResponse:
    id: int | None = None
    artist: str
    title: str
    is_synced: bool = False
    synced_text: dict | None = None
    plain_text: str | None = None
    language: str = "und"
    offset: int = 0


@dataclass(slots=True)
class MusicVideo:
    id: int | None = None
    local_link: str
    track_id: int


@dataclass(slots=True)
class User:
    id: int | None = None
    username: str
    password: str
    email: str
    api_key: str | None = None
    is_admin: bool = False
