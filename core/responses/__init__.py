from dataclasses import dataclass, field
from datetime import datetime


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
    duration: int | None = None


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
class ShortPlaylistResponse:
    id: int
    title: str
    is_public: bool
    owners: list[ShortUserResponse]
    tracks_count: int
    duration: int
    created_at: datetime
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
class ShortToolResponse:
    tool_id: str
    tool_name: str
