from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class Artist:
    name: str
    albums: list[Album]
    id: int | None = None
    cover_path: int | None = None
    external_id: int | None = None


@dataclass(slots=True)
class ArtistShort:
    name: str
    id: int | None = None
    cover_path: int | None = None
    external_id: int | None = None


@dataclass(slots=True)
class Album:
    title: str
    duration: int
    tracks_count: int
    tracks: list[Track]
    artist: ArtistShort | None = None
    id: int | None = None
    cover_path: int | None = None
    created_at: datetime | None = None
    external_id: int | None = None


@dataclass(slots=True)
class AlbumShort:
    title: str
    duration: int
    tracks_count: int
    tracks: list[Track]
    artist: ArtistShort | None = None
    id: int | None = None
    cover_path: int | None = None
    created_at: datetime | None = None
    external_id: int | None = None


@dataclass(slots=True)
class Playlist:
    title: str
    tracks: list[Track]
    owner: User
    tracks_count: int
    duration: int
    id: int | None = None
    cover_path: int | None = None
    is_public: bool = False
    created_at: datetime | None = None


@dataclass(slots=True)
class Track:
    title: str
    length: int
    lyrics: list[Lyrics]
    music_videos: list[MusicVideo]
    artists: list[ArtistShort]
    id: int | None = None
    album: Album | None = None
    cover_path: int | None = None
    path: str | None = None
    album_position: int | None = None
    bpm: int | None = None
    track_gain: float | None = None
    track_peak: float | None = None
    disc_number: int | None = None
    year: int | None = None
    created_at: datetime | None = None
    external_id: int | None = None


@dataclass(slots=True)
class TrackShort:
    title: str
    length: int
    id: int | None = None
    cover_path: int | None = None
    path: str | None = None
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
    language: str
    path: int
    offset: int = 0
    id: int | None = None
    is_synced: bool = False
    synced_text: dict | None = None
    plain_text: str | None = None
    type: str | None = None
    track_id: int | None = None


@dataclass(slots=True)
class LyricsResponse:
    artist: str
    title: str
    id: int | None = None
    is_synced: bool = False
    synced_text: dict | None = None
    plain_text: str | None = None
    language: str = "und"
    offset: int = 0


@dataclass(slots=True)
class MusicVideo:
    local_link: int
    track_id: int
    id: int | None = None


@dataclass(slots=True)
class User:
    username: str
    password: str
    email: str
    id: int | None = None
    is_admin: bool = False


@dataclass(slots=True)
class ObjectStorage:
    link_type: str
    link_provider: str
    link: str
    id: int | None = None
    created_at: datetime | None = None
    track_id: int | None = None
    music_video_id: int | None = None
    lyrics_id: int | None = None
