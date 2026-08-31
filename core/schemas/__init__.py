from __future__ import annotations
from concurrent.futures import Future
from dataclasses import dataclass, field
from datetime import datetime
from typing import NamedTuple
from enum import Enum


@dataclass(slots=True)
class Artist:
    name: str
    id: int | None = None
    description: str | None = None
    cover_path: int | None = None
    external_id: str | None = None
    created_at: datetime | None = None
    genres: list[str] = field(default_factory=list)
    albums: list[Album] = field(default_factory=list)


@dataclass(slots=True)
class Mood:
    name: str
    id: int | None = None
    tracks: list[TrackShort] = field(default_factory=list)


@dataclass(slots=True)
class Genre:
    name: str
    id: int | None = None
    artists: list[ArtistShort] = field(default_factory=list)
    albums: list[AlbumShort] = field(default_factory=list)
    tracks: list[TrackShort] = field(default_factory=list)


@dataclass(slots=True)
class ArtistShort:
    name: str
    id: int | None = None
    description: str | None = None
    cover_path: int | None = None
    external_id: str | None = None
    created_at: datetime | None = None
    genres: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Album:
    title: str
    album_type: str | None = None
    duration: int | None = None
    year: int | None = None
    tracks_count: int | None = None
    description: str | None = None
    id: int | None = None
    cover_path: int | None = None
    created_at: datetime | None = None
    external_id: str | None = None
    tracks: list[Track] = field(default_factory=list)
    artists: list[ArtistShort] = field(default_factory=list)
    genres: list[str] = field(default_factory=list)


@dataclass(slots=True)
class AlbumShort:
    title: str
    duration: int | None = None
    tracks_count: int | None = None
    album_type: str | None = None
    description: str | None = None
    id: int | None = None
    cover_path: int | None = None
    created_at: datetime | None = None
    external_id: str | None = None
    tracks: list[TrackShort] = field(default_factory=list)
    artists: list[ArtistShort] = field(default_factory=list)
    genres: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Playlist:
    title: str
    owners: list[User]
    tracks_count: int
    duration: int
    id: int | None = None
    cover_path: int | None = None
    is_public: bool = False
    created_at: datetime | None = None
    tracks: list[Track] = field(default_factory=list)


@dataclass(slots=True)
class Track:
    title: str
    length: int
    id: int | None = None
    cover_path: int | None = None
    path: int | None = None
    bpm: int | None = None
    track_gain: float | None = None
    track_peak: float | None = None
    year: int | None = None
    created_at: datetime | None = None
    external_id: str | None = None
    artists: list[ArtistShort] = field(default_factory=list)
    albums: list[TrackAlbum] = field(default_factory=list)
    lyrics: list[Lyrics] = field(default_factory=list)
    music_videos: list[MusicVideo] = field(default_factory=list)


@dataclass(slots=True)
class TrackShort:
    title: str
    length: int
    id: int | None = None
    cover_path: int | None = None
    path: int | None = None
    bpm: int | None = None
    track_gain: float | None = None
    track_peak: float | None = None
    year: int | None = None
    created_at: datetime | None = None
    external_id: str | None = None
    albums: list[TrackAlbum] = field(default_factory=list)
    artists: list[ArtistShort] = field(default_factory=list)


@dataclass(slots=True)
class Lyrics:
    language: str
    path: int | None
    offset: int = 0
    id: int | None = None
    is_synced: bool = False
    synced_text: list[dict] | None = None
    plain_text: str | None = None
    type: str | None = None
    track_id: int | None = None


@dataclass(slots=True)
class MusicVideo:
    local_link: int | None
    track_id: int
    duration_ms: int | None = None
    id: int | None = None


@dataclass(slots=True)
class StoredUser:
    username: str
    password: str
    email: str
    id: int
    is_admin: bool = False


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


@dataclass(slots=True)
class ShortTrackInfo:
    title: str
    album: str
    artists: list[str]


@dataclass(slots=True)
class TrackAlbumMetadata:
    title: str
    album_artists: list[str]
    disc_number: int | None = None
    album_position: int | None = None


@dataclass(slots=True)
class TrackMetadata:
    title: str | None
    length: int | None = None
    year: int | None = None
    bitrate: int | None = None
    bpm: int | None = None
    artists: list[str] = field(default_factory=list)
    albums: list[TrackAlbumMetadata] = field(default_factory=list)
    genres: list[str] = field(default_factory=list)
    moods: list[str] = field(default_factory=list)


@dataclass(slots=True)
class TrackAlbum:
    title: str
    duration: int | None = None
    tracks_count: int | None = None
    id: int | None = None
    cover_path: int | None = None
    created_at: datetime | None = None
    disc_number: int | None = None
    album_position: int | None = None
    is_primary: bool = False
    external_id: str | None = None
    artists: list[ArtistShort] = field(default_factory=list)


@dataclass(slots=True)
class HealthStatus:
    ok: bool
    message: str | None = None


@dataclass(slots=True)
class ServicesStatus:
    downloaders: list[ServiceStatus]
    importers: list[ServiceStatus]
    scrobblers: list[ServiceStatus]
    search: list[ServiceStatus]
    storages: list[ServiceStatus]


@dataclass(slots=True)
class ServiceStatus:
    tag: str
    health: HealthStatus


@dataclass(slots=True)
class SearchResults:
    artists: list[Artist]
    albums: list[Album]
    tracks: list[Track]


class BinaryBlob(NamedTuple):
    content: bytes
    mime: str


class FilePathInfo(NamedTuple):
    link: str
    filename: str


class AlbumType(str, Enum):
    ALBUM = "album"
    EP = "ep"
    SINGLE = "single"
    COMPILATION = "compilation"


@dataclass(slots=True)
class LibraryStats:
    tracks_total: int
    tracks_with_lyrics: int
    tracks_with_videos: int
    albums_total: int
    albums_with_cover: int
    artists_total: int
    artists_with_cover: int
    lyrics_total: int
    videos_total: int
    genres_total: int
    artists_with_genres: int
    albums_with_genres: int
    tracks_with_genres: int
    moods_total: int
    tracks_with_moods: int


@dataclass(slots=True)
class StartStatuses:
    downloaders: list[ServiceStatus] = field(default_factory=list)
    importers: list[ServiceStatus] = field(default_factory=list)
    search: list[ServiceStatus] = field(default_factory=list)
    storages: list[ServiceStatus] = field(default_factory=list)
    scrobblers: list[ServiceStatus] = field(default_factory=list)


@dataclass(slots=True)
class ApiKey:
    key: str
    user_id: int
    revoked: bool = False
    id: int | None = None
    created_at: datetime | None = None


@dataclass(slots=True)
class ProviderKey:
    provider: str
    key: str
    user_id: int
    id: int | None = None
    created_at: datetime | None = None


@dataclass(slots=True)
class LRCLyrics:
    artist: str
    album: str
    title: str
    offset: int
    text: list[dict[str, int | str]]
