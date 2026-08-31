import tomllib
from pathlib import Path
from core.schemas import ApiKey, ProviderKey, BinaryBlob, ServicesStatus, LibraryStats, SearchResults
from core.errors import BaseError
from core.responses import FullTrackResponse, FullAlbumResponse, FullArtistResponse, ShortTrackResponse, ShortToolResponse, ShortArtistResponse, ShortAlbumResponse, FullPlaylistResponse, ShortUserResponse, ListedUserResponse, LyricsResponse
from typing import Literal, Generator, overload
from core.services import album_service, artist_service, playlist_service, server_service, track_service, user_service
from core.modules.downloaders.downloaders_manager import DownloadManager
QueueName = Literal["download", "sync", "importing"]


class LibraryManager:
    def __init__(self) -> None:
        path = Path(__file__).resolve()
        self.config_path = path.parents[1] / "config.toml"
        self.toml_config = ""
        with self.config_path.open("r", encoding="utf-8") as config_file:
            self.toml_config = config_file.read()
            self.config = tomllib.loads(self.toml_config)
        self.start_errors: StartStatuses = StartStatuses()
        self.db_manager = DBManager()
        self.logger: BoundLogger = get_logger(__name__)

    def local_search(
        self,
        query: str,
        artistCount: int,
        artistOffset: int,
        albumCount: int,
        albumOffset: int,
        songCount: int,
        songOffset: int,
    ) -> SearchResults:
        with self.db_manager.get_session() as session:
            server_service.local_search()
    def global_search(self, query: str) -> SearchResults:
        with self.db_manager.get_session() as session:
        
    @overload
    def get_global_object(
        self, object_type: Literal["track"], object_id: str
    ) -> FullTrackResponse | BaseError: ...
    @overload
    def get_global_object(
        self, object_type: Literal["album"], object_id: str
    ) -> FullAlbumResponse | BaseError: ...
    @overload
    def get_global_object(
        self, object_type: Literal["artist"], object_id: str
    ) -> FullArtistResponse | BaseError: ...

    def get_global_object(
        self, object_type: Literal["track", "album", "artist"], object_id: str
    ):
        with self.db_manager.get_session() as session:
    def get_similiar_artists_random_tracks(
        self, artist_id: int, count: int
    ) -> list[ShortTrackResponse] | BaseError:
        with self.db_manager.get_session() as session:

    def get_track_tools(self) -> list[ShortToolResponse]:
        return self.tools_manager.get_track_process_events()

    def process_track(self, tool_func_id: str, track_id: int) -> BaseError | None:
        with self.db_manager.get_session() as session:
            track = self.db_manager.get_track_by_id(session, track_id)
            if isinstance(track, BaseError):
                return NotFoundError()
            return self.tools_manager.send_event(
                Event.PROCESS_TRACK, track=track, tool_func_id=tool_func_id
            )

    def get_user_tracks_recommendations(
        self, user_id: int, count: int
    ) -> list[ShortTrackResponse] | BaseError:
        with self.db_manager.get_session() as session:

    def download(
        self,
        task_id: str | None = None,
        query: str | None = None,
        object_id: str | None = None,
    ) -> str:
        task_id = self.post_task(
            func=self.download_track,
            queue_name="download",
            task_id=task_id,
            query=query,
            object_id=object_id,
        )
        self.task_queue.download[task_id].result = DownloadTaskResult()
        return task_id

    def download_track(
        self,
        task_id: str,
        query: str | None = None,
        object_id: str | None = None,
    ):
        DownloadManager.download_track(task_id=task_id,query=query,object_id=object_id)

    def get_file(self, path: str, storage_id: str) -> bytes | None:
        with self.db_manager.get_session() as session:
    def get_all_tracks(self) -> list[ShortTrackResponse]:
        with self.db_manager.get_session() as session:

    def get_all_artists(
        self, size: int | None = None, offset: int | None = None
    ) -> list[ShortArtistResponse]:
        with self.db_manager.get_session() as session:
    def get_all_albums(
        self, size: int = 10, offset: int = 0
    ) -> list[ShortAlbumResponse]:
        with self.db_manager.get_session() as session:

    def get_track_by_id(self, id: int) -> FullTrackResponse | BaseError:
        with self.db_manager.get_session() as session:

    def scrobble(
        self, id: int, user_id: int, listen_time: int | None = None
    ) -> BaseError | None:
        with self.db_manager.get_session() as session:

    def post_now_playing(self, id: int, user_id: int) -> BaseError | None:
        with self.db_manager.get_session() as session:

    def delete_provider_key(self, key_id: int):
        with self.db_manager.get_session() as session:

    def get_provider_types(self) -> list[str]:
        return [scrobbler.tag for scrobbler in self.scrobblers]

    def create_api_key(self, user_id: int) -> ApiKey | BaseError:
        with self.db_manager.get_session() as session:

    def create_provider_key(
        self, user_id: int, key: str, provider: str
    ) -> ProviderKey | BaseError:
        with self.db_manager.get_session() as session:

    def change_provider_key(
        self, user_id: int, key_id: int, new_key: str
    ) -> BaseError | None:
        with self.db_manager.get_session() as session:

    def check_api_key_availability(self, api_key: str) -> ApiKey | BaseError:
        with self.db_manager.get_session() as session:

    def get_user_provider_keys(self, user_id: int) -> list[ProviderKey]:
        with self.db_manager.get_session() as session:

    def get_user_api_keys(self, user_id: int) -> list[ApiKey]:
        with self.db_manager.get_session() as session:

    def revoke_api_key(self, key_id: int):
        with self.db_manager.get_session() as session:

    def get_similiar_artists(self, id: int, count: int = 5) -> list[ShortArtistResponse] | BaseError:
        with self.db_manager.get_session() as session:

    def get_album_by_id(self, id: int) -> FullAlbumResponse | BaseError:
        with self.db_manager.get_session() as session:
    def get_artist_by_id(self, id: int) -> FullArtistResponse | BaseError:
        with self.db_manager.get_session() as session:

    def get_artist_top_songs(self, name: str, count: int) -> list[ShortTrackResponse]:
        with self.db_manager.get_session() as session:
    def get_cover_art(self, id: int) -> BinaryBlob | BaseError:
        with self.db_manager.get_session() as session:
    def get_genres(self) -> list[dict[str, str | int]]:
        with self.db_manager.get_session() as session:
    def get_moods(self) -> list[dict[str, str | int]]:
        with self.db_manager.get_session() as session:

    def get_playlist_by_id(self, id: int) -> FullPlaylistResponse | BaseError:
        with self.db_manager.get_session() as session:

    def delete_user_by_username(self, username: str, user_id: int) -> int | BaseError:
        with self.db_manager.get_session() as session:

    def delete_user_by_id(self, id: int, user_id: int) -> int | BaseError:
        with self.db_manager.get_session() as session:

    #def delete_track(self, track_id: int):


    def star(self, user_id: int, object_id: int, object_type: str) -> BaseError | None:
        with self.db_manager.get_session() as session:

    def unstar(
        self, user_id: int, object_id: int, object_type: str
    ) -> BaseError | None:
        with self.db_manager.get_session() as session:

    def get_user_playlists(
        self, user_id: int, size: int = 10, offset: int = 0
    ) -> list[FullPlaylistResponse]:
        with self.db_manager.get_session() as session:
    def create_playlist(
        self,
        user_id: int,
        title: str,
        tracks_id: list[int],
        is_public: bool = False,
        cover_path: int | None = None,
    ) -> FullPlaylistResponse | BaseError:
        with self.db_manager.get_session() as session:
    def get_config(self) -> str:
        return self.toml_config

    def change_config(self, new_config: str):
        new_dict = tomllib.loads(new_config)

        with self.config_path.open("w", encoding="utf-8") as file:
            file.write(new_config)

        self.toml_config = new_config
        self.config = new_dict

    def update_user_by_username(
        self,
        acting_user_id: int,
        current_username: str,
        new_username: str | None = None,
        new_password: str | None = None,
        set_is_admin: bool | None = None,
    ) -> ShortUserResponse | BaseError:
        with self.db_manager.get_session() as session:
    def update_user_by_id(
        self,
        acting_user_id: int,
        changed_user_id: int,
        new_username: str | None = None,
        new_password: str | None = None,
        set_is_admin: bool | None = None,
    ) -> ShortUserResponse | BaseError:
        with self.db_manager.get_session() as session:
    def create_user(
        self, username: str, email: str, password: str
    ) -> ListedUserResponse:
        with self.db_manager.get_session() as session:

    def delete_playlist(self, playlist_id: int):
        with self.db_manager.get_session() as session:

    def update_playlist(
        self,
        playlist_id: int,
        user_id: int,
        title: str | None,
        track_ids: list[int] | None,
        owner_ids: list[int] | None,
        is_public: bool | None,
    ) -> FullPlaylistResponse | BaseError:
        with self.db_manager.get_session() as session:
    def get_all_user_starred(
        self, user_id: int
    ) -> tuple[list[ShortTrackResponse], list[ShortAlbumResponse], list[ShortArtistResponse]] | None:
        with self.db_manager.get_session() as session:
    def get_track_by_title(self, title: str) -> FullTrackResponse | BaseError:
        with self.db_manager.get_session() as session:

    def get_lyrics(self, track_id: int) -> list[LyricsResponse] | BaseError:
        with self.db_manager.get_session() as session:

    def get_user(
        self, username: str | None = None, user_id: int | None = None
    ) -> ListedUserResponse | None | BaseError:
        with self.db_manager.get_session() as session:

    def stream_track(
        self, id: str, start_bytes: int, end_bytes: int
    ) -> Generator[bytes] | BaseError:
        with self.db_manager.get_session() as session:

    def get_albums_cursor(
        self, cursor: str | None, limit: int = 20
    ) -> tuple[list[ShortAlbumResponse], str | None]:
        with self.db_manager.get_session() as session:
    def get_artists_cursor(
        self, cursor: str | None, limit: int = 20
    ) -> tuple[list[ShortArtistResponse], str | None]:
        with self.db_manager.get_session() as session:

    def get_tracks_cursor(
        self, cursor: str | None, limit: int = 20
    ) -> tuple[list[ShortTrackResponse], str | None]:
        with self.db_manager.get_session() as session:

    def get_file_metadata(self, id: str) -> dict | BaseError:
        with self.db_manager.get_session() as session:

    def get_sync_task(self, task_id: str) -> Task[SyncTaskResult] | BaseError:
        task = self.task_queue.sync.get(task_id, NotFoundError())
        return task

    def cancel_sync_task(self, task_id: str) -> bool | BaseError:
        task = self.task_queue.sync.get(task_id)
        if task is None:
            return NotFoundError()
        return task.task.cancel()

    def get_download_task(self, task_id: str) -> Task[DownloadTaskResult] | BaseError:
        task = self.task_queue.download.get(task_id, NotFoundError())
        return task

    def cancel_download_task(self, task_id: str) -> bool | BaseError:
        task = self.task_queue.download.get(task_id)
        if task is None:
            return NotFoundError()
        return task.task.cancel()

    def get_import_task(self, task_id: str) -> Task[ImportTaskResult] | BaseError:
        task = self.task_queue.importing.get(task_id, NotFoundError())
        return task

    def post_task(
        self, func, queue_name: QueueName, task_id: str | None = None, *args, **kwargs
    ) -> str:
        task_id = str(uuid4())[:8] if task_id is None else task_id
        task_body = self.executor.submit(func, task_id, *args, **kwargs)
        target = getattr(self.task_queue, queue_name)
        target[task_id] = Task(task=task_body)
        return task_id


    def sync(self, task_id: str | None = None) -> str:
        task_id = self.post_task(self.sync_library, task_id=task_id, queue_name="sync")
        self.task_queue.sync[task_id].result = SyncTaskResult()
        return task_id

    def sync_library(self, task_id: str):
        with self.db_manager.get_session() as session:

    def import_library(
        self,
        task_id: str | None = None,
        importer_tag: str | None = None,
        user_id: int | None = None,
    ) -> str:
        task_id = self.post_task(
            func=self.import_tracks,
            queue_name="importing",
            task_id=task_id,
            importer_tag=importer_tag,
            user_id=user_id,
        )
        self.task_queue.importing[task_id].result = ImportTaskResult()
        return task_id

    def import_tracks(
        self, task_id: str, importer_tag: str, user_id: int | None = None
    ):
        with self.db_manager.get_session() as session:

    def get_all_users(self) -> list[ListedUserResponse]:
        with self.db_manager.get_session() as session:

    def check_status(self) -> ServicesStatus:
         with self.db_manager.get_session() as session:

    def get_library_stats(self) -> LibraryStats:
        with self.db_manager.get_session() as session:
