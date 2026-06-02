from __future__ import annotations
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
    genres: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Album:
    title: str
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
    path: str | None = None
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
    path: str | None = None
    bpm: int | None = None
    track_gain: float | None = None
    track_peak: float | None = None
    year: int | None = None
    created_at: datetime | None = None
    external_id: str | None = None
    albums: list[TrackAlbum] = field(default_factory=list)


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
    duration_ms: int | None = None
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


@dataclass(slots=True)
class ImporterArtist:
    id: int | str
    name: str
    cover_uri: str | None = None
    description: str | None = None
    genres: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ImporterPlaylistTrack:
    id: int | str
    playlist_position: int


@dataclass(slots=True)
class ImporterPlaylist:
    id: int | str
    title: str
    tracks: list[ImporterPlaylistTrack]
    cover_uri: str | None = None


@dataclass(slots=True)
class Task[T]:
    result: T | None = None
    progress: int = 0
    status: str = "processing"
    error: str | None = None


class AlbumType(str, Enum):
    ALBUM = "album"
    EP = "ep"
    SINGLE = "single"
    COMPILATION = "compilation"


@dataclass(slots=True)
class DownloadTaskResult:
    title: str
    artist: list[str]
    length: int
    storage: str
    download_source: str
    saved_path: str


@dataclass(slots=True)
class SyncMetric:
    searched_new: int = 0
    processed: int = 0
    added: int = 0
    deleted: int = 0


@dataclass(slots=True)
class UnboundFiles:
    covers: set[tuple[str, str]] = field(default_factory=set)
    lyrics: set[tuple[str, str]] = field(default_factory=set)
    videos: set[tuple[str, str]] = field(default_factory=set)


@dataclass(slots=True)
class SyncTaskResult:
    tracks: SyncMetric = field(default_factory=SyncMetric)
    covers: SyncMetric = field(default_factory=SyncMetric)
    lyrics: SyncMetric = field(default_factory=SyncMetric)
    videos: SyncMetric = field(default_factory=SyncMetric)
    unbound_files: UnboundFiles = field(default_factory=UnboundFiles)


@dataclass(slots=True)
class ImportMetric:
    searched: int = 0
    saved: int = 0


@dataclass(slots=True)
class ImportTaskResult:
    tracks: ImportMetric = field(default_factory=ImportMetric)
    covers: ImportMetric = field(default_factory=ImportMetric)
    videos: ImportMetric = field(default_factory=ImportMetric)
    lyrics: ImportMetric = field(default_factory=ImportMetric)
    albums: ImportMetric = field(default_factory=ImportMetric)
    artists: ImportMetric = field(default_factory=ImportMetric)
    playlists: ImportMetric = field(default_factory=ImportMetric)


@dataclass(slots=True)
class ImporterAlbum:
    id: int | str
    artist_ids: list[int | str]
    artists: list[str]
    title: str
    year: int | None = None
    cover_uri: str | None = None
    description: str | None = None
    album_type: AlbumType = field(default=AlbumType.ALBUM)
    genres: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ImporterTrack(TrackMetadata):
    id: int | str | None = None
    artist_ids: list[str | int] = field(default_factory=list)
    album_ids: list[str | int] = field(default_factory=list)
    has_lyrics: bool = False
    has_video: bool = False


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
