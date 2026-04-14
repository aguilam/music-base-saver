from dataclasses import dataclass
from __future__ import annotations


@dataclass(slots=True)
class Artist:
    id: int | None
    external_id: int | None
    name: str
    cover_path: str | None


@dataclass(slots=True)
class Album:
    id: int | None
    external_id: int | None
    title: str
    cover_path: str | None
    duration: int
    tracks_count: int
    artist: Artist
    tracks: list[Track] | None


@dataclass(slots=True)
class Playlist:
    id: int | None
    title: str
    cover_path: str | None
    tracks: list[Track] | None
    is_public: bool
    tracks_count: int
    duration: int


@dataclass(slots=True)
class Track:
    id: int | None
    external_id: int | None
    title: str
    artists: list[Artist] | None
    album: Album | None
    cover_path: str | None
    path: str
    length: int
    album_position: int | None
    bpm: int | None
    track_gain: float | None
    track_peak: float | None
    disc_number: int | None
    year: int | None


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
class MusicVideo:
    id: int | None
    local_link: str
    track_id: int
