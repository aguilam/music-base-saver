from core.schemas import AlbumType, TrackMetadata
from dataclasses import dataclass, field


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
