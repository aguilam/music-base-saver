from asyncio.futures import Future
from dataclasses import dataclass, field


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
class UnboundFiles:
    covers: set[tuple[str, str]] = field(default_factory=set)
    lyrics: set[tuple[str, str]] = field(default_factory=set)
    videos: set[tuple[str, str]] = field(default_factory=set)


@dataclass(slots=True)
class SyncMetric:
    searched_new: int = 0
    processed: int = 0
    added: int = 0
    deleted: int = 0


@dataclass(slots=True)
class SyncTaskResult:
    tracks: SyncMetric = field(default_factory=SyncMetric)
    covers: SyncMetric = field(default_factory=SyncMetric)
    lyrics: SyncMetric = field(default_factory=SyncMetric)
    videos: SyncMetric = field(default_factory=SyncMetric)
    unbound_files: UnboundFiles = field(default_factory=UnboundFiles)


@dataclass(slots=True)
class DownloadTaskResult:
    title: str = ""
    artist: list[str] = field(default_factory=list)
    length: int = 0
    storage: str = ""
    download_source: str = ""
    saved_path: str = ""


@dataclass(slots=True)
class Task[T]:
    result: T = field(init=False)
    task: Future
    progress: int = 0
    status: str = "processing"
    error: str | None = None


@dataclass(slots=True)
class TaskStorage:
    download: dict[str, Task[DownloadTaskResult]] = field(default_factory=dict)
    sync: dict[str, Task[SyncTaskResult]] = field(default_factory=dict)
    importing: dict[str, Task[ImportTaskResult]] = field(default_factory=dict)
