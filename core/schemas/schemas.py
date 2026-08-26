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
class ShortArtistResponse:
    id: int
    name: str
    albums_count: int
    created_at: datetime
    cover_id: int | None = None
    external_id: str | None = None


@dataclass(slots=True)
class ShortAlbumResponse:
    id: int
    title: str
    created_at: datetime
    cover_id: int | None = None
    year: int | None = None
    external_id: str | None = None
    artists: list[ShortArtistResponse] = field(default_factory=list)


@dataclass(slots=True)
class ShortUserResponse:
    id: int
    username: str


@dataclass(slots=True)
class ListedUserResponse:
    id: int
    username: str
    is_admin: bool


@dataclass(slots=True)
class ShortPlaylistResponse:
    id: int
    title: str
    owners: list[ShortUserResponse]
    public: bool
    created_at: datetime
    tracks_count: int
    duration: int
    cover_id: int | None = None


@dataclass(slots=True)
class ShortTrackResponse:
    id: int
    title: str
    duration: int
    created_at: datetime | None = None
    cover_id: int | None = None
    bpm: int | None = None
    track_gain: float | None = None
    track_peak: float | None = None
    year: int | None = None
    external_id: str | None = None
    artists: list[ShortArtistResponse] = field(default_factory=list)


@dataclass(slots=True)
class ShortLyricsResponse:
    id: int
    language: str
    track_id: int
    offset: int
    is_synced: bool
    synced_text: list[dict] | None = None
    plain_text: str | None = None


@dataclass(slots=True)
class ShortMusicVideoResponse:
    id: int
    track_id: int
    duration_ms: int | None = None


# TODO: Add short album
@dataclass(slots=True)
class FullTrackResponse:
    id: int
    title: str
    duration: int
    created_at: datetime
    cover_id: int | None = None
    bpm: int | None = None
    track_gain: float | None = None
    track_peak: float | None = None
    year: int | None = None
    external_id: str | None = None
    artists: list[ShortArtistResponse] = field(default_factory=list)
    lyrics: list[ShortLyricsResponse] = field(default_factory=list)
    music_videos: list[ShortMusicVideoResponse] = field(default_factory=list)


@dataclass(slots=True)
class FullAlbumResponse:
    id: int
    title: str
    duration: int
    tracks_count: int
    created_at: datetime
    album_type: str | None = None
    year: int | None = None
    description: str | None = None
    cover_id: int | None = None
    external_id: str | None = None
    tracks: list[ShortTrackResponse] = field(default_factory=list)
    artists: list[ShortArtistResponse] = field(default_factory=list)
    genres: list[str] = field(default_factory=list)
    moods: list[str] = field(default_factory=list)


@dataclass(slots=True)
class FullPlaylistResponse:
    id: int
    title: str
    is_public: bool
    owners: list[ShortUserResponse]
    tracks_count: int
    duration: int
    created_at: datetime
    tracks: list[ShortTrackResponse] = field(default_factory=list)
    cover_id: int | None = None


@dataclass(slots=True)
class FullArtistResponse:
    id: int
    name: str
    albums_count: int
    created_at: datetime
    description: str | None = None
    cover_id: int | None = None
    external_id: str | None = None
    genres: list[str] = field(default_factory=list)
    albums: list[ShortAlbumResponse] = field(default_factory=list)


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
class LyricsResponse:
    artist: str
    title: str
    id: int | None = None
    is_synced: bool = False
    synced_text: list[dict] | None = None
    plain_text: str | None = None
    language: str = "und"
    offset: int = 0


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
    result: T = field(init=False)
    task: Future
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
    title: str = ""
    artist: list[str] = field(default_factory=list)
    length: int = 0
    storage: str = ""
    download_source: str = ""
    saved_path: str = ""


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
class TaskStorage:
    download: dict[str, Task[DownloadTaskResult]] = field(default_factory=dict)
    sync: dict[str, Task[SyncTaskResult]] = field(default_factory=dict)
    importing: dict[str, Task[ImportTaskResult]] = field(default_factory=dict)


@dataclass(slots=True)
class LRCLyrics:
    artist: str
    album: str
    title: str
    offset: int
    text: list[dict[str, int | str]]
