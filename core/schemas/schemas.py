from dataclasses import dataclass


@dataclass(slots=True)
class Track:
    id: int | None
    title: str
    artists_names: list[str] | None
    artists_id: list[int]
    album_name: str
    album_id: int
    cover_path: str | None
    path: str
    length: int
    album_position: int | None
    bpm: int | None
    trackGain: float | None
    trackPeak: float | None
    discNumber: int | None
    year: int | None


@dataclass(slots=True)
class Artist:
    id: int | None
    name: str
    cover_path: str | None


@dataclass(slots=True)
class Album:
    id: int | None
    title: str
    cover_path: str | None
    duration: int
    tracks_count: int
    Artist: Artist
    tracks: list[Track] | None


@dataclass(slots=True)
class Playlist:
    id: int | None
    title: str
    cover_path: str | None
    tracks: list[Track] | None
    public: bool
    tracks_count: int
    duration: int


@dataclass(slots=True)
class Lyric:
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
