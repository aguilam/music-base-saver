from core.modules.storages.schemas import FileMetadata
from core.modules.importers.importers_manager import ImportersManager
from core.tasks.schemas import (
    DownloadTaskResult,
    ImportTaskResult,
    SyncTaskResult,
    Task,
)
from core.tasks.tasks_manager import TasksManager
from core.modules.storages.storages_manager import StoragesManager
from core.modules.tools.events import Event
from core.modules.tools.tools_manager import ToolsManager
from core.responses.mappers import (
    to_short_track_response,
    to_short_album_response,
    to_short_artist_response,
    to_full_track_response,
    to_full_playlist_response,
    to_short_user_response,
    to_full_artist_response,
    to_full_album_response,
    to_short_playlist_response,
)
from core.modules.scrobblers.scrobblers_manager import ScrobblersManager
from core.modules.searches.searches_manager import SearchesManager
from core.db.manager import DBManager
import tomllib
from pathlib import Path
from core.schemas import (
    ApiKey,
    ProviderKey,
    BinaryBlob,
    ServicesStatus,
    LibraryStats,
    StoredUser,
)
from core.errors import BaseError, check_error, NotFoundError, UnauthorizedError
from core.responses import (
    FullTrackResponse,
    FullAlbumResponse,
    FullArtistResponse,
    ShortTrackResponse,
    ShortToolResponse,
    ShortArtistResponse,
    ShortAlbumResponse,
    FullPlaylistResponse,
    ShortUserResponse,
    LyricsResponse,
    ShortPlaylistResponse,
    SearchResultsResponse,
)
from typing import Literal, overload
from collections.abc import Iterator
from core.services import (
    album_service,
    artist_service,
    playlist_service,
    server_service,
    track_service,
    user_service,
)
from core.modules.downloaders.downloaders_manager import DownloadManager


class LibraryManager:
    def __init__(self) -> None:
        path = Path(__file__).resolve()
        self.config_path = path.parents[1] / "config.toml"
        self.toml_config = ""
        with self.config_path.open("r", encoding="utf-8") as config_file:
            self.toml_config = config_file.read()
            self.config = tomllib.loads(self.toml_config)

    def local_search(
        self,
        query: str,
        artistCount: int,
        artistOffset: int,
        albumCount: int,
        albumOffset: int,
        songCount: int,
        songOffset: int,
    ) -> SearchResultsResponse:
        with DBManager.get_session() as session:
            searched = server_service.local_search(
                session,
                query,
                artistCount,
                artistOffset,
                albumCount,
                albumOffset,
                songCount,
                songOffset,
            )
            return SearchResultsResponse(
                artists=[
                    to_short_artist_response(artist) for artist in searched.artists
                ],
                albums=[to_short_album_response(album) for album in searched.albums],
                tracks=[to_short_track_response(track) for track in searched.tracks],
            )

    def global_search(self, query: str) -> SearchResultsResponse:
        searched = SearchesManager.global_search(query)
        return SearchResultsResponse(
            artists=[to_short_artist_response(artist) for artist in searched.artists],
            albums=[to_short_album_response(album) for album in searched.albums],
            tracks=[to_short_track_response(track) for track in searched.tracks],
        )

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
        return SearchesManager.get_global_object(object_type, object_id)

    def get_similiar_artists_random_tracks(
        self, artist_id: int, count: int
    ) -> list[ShortTrackResponse] | BaseError:
        tracks = ScrobblersManager.get_similiar_artists_random_tracks(artist_id, count)
        if isinstance(tracks, BaseError):
            return tracks
        return [to_short_track_response(track) for track in tracks]

    def get_track_tools(self) -> list[ShortToolResponse]:
        return ToolsManager.get_track_process_events()

    def process_track(self, tool_func_id: str, track_id: int) -> BaseError | None:
        with DBManager.get_session() as session:
            track = track_service.get_track_by_id(session, track_id)
            if isinstance(track, BaseError):
                return NotFoundError()
            return ToolsManager.send_event(
                Event.PROCESS_TRACK, track=track, tool_func_id=tool_func_id
            )

    def get_user_tracks_recommendations(
        self, user_id: int, count: int
    ) -> list[ShortTrackResponse] | BaseError:
        tracks = ScrobblersManager.get_user_tracks_recommendations(user_id, count)
        if isinstance(tracks, BaseError):
            return tracks
        return [to_short_track_response(track) for track in tracks]

    def download(
        self,
        task_id: str | None = None,
        query: str | None = None,
        object_id: str | None = None,
    ) -> str:
        task_id = TasksManager.post_task(
            func=DownloadManager.download_track,
            queue_name="download",
            task_id=task_id,
            query=query,
            task_result=DownloadTaskResult(),
            object_id=object_id,
        )
        return task_id

    def get_all_tracks(self) -> list[ShortTrackResponse]:
        with DBManager.get_session() as session:
            tracks = track_service.get_all_tracks(session)
            return [to_short_track_response(track) for track in tracks]

    def get_all_artists(
        self, size: int | None = None, offset: int | None = None
    ) -> list[ShortArtistResponse]:
        with DBManager.get_session() as session:
            artists = artist_service.get_all_artists(session)
            return [to_short_artist_response(artist) for artist in artists]

    def get_all_albums(
        self, size: int = 10, offset: int = 0
    ) -> list[ShortAlbumResponse]:
        with DBManager.get_session() as session:
            albums = album_service.get_all_albums(session, size, offset)
            return [to_short_album_response(album) for album in albums]

    def get_track_by_id(self, id: int) -> FullTrackResponse | BaseError:
        with DBManager.get_session() as session:
            track = track_service.get_track_by_id(session, id)
            return check_error(track, to_full_track_response)

    def scrobble(
        self, id: int, user_id: int, listen_time: int | None = None
    ) -> BaseError | None:
        return ScrobblersManager.scrobble(id, user_id, listen_time)

    def post_now_playing(self, id: int, user_id: int) -> BaseError | None:
        return ScrobblersManager.post_now_playing(id, user_id)

    def delete_provider_key(self, key_id: int):
        with DBManager.get_session() as session:
            return user_service.delete_provider_key(session, key_id)

    def get_provider_types(self) -> list[str]:
        return [scrobbler.tag for scrobbler in ScrobblersManager.scrobblers]

    def create_api_key(self, user_id: int) -> ApiKey | BaseError:
        with DBManager.get_session() as session:
            return user_service.create_api_key(session, user_id)

    def create_provider_key(
        self, user_id: int, key: str, provider: str
    ) -> ProviderKey | BaseError:
        with DBManager.get_session() as session:
            return user_service.create_provider_key(session, user_id, key, provider)

    def change_provider_key(
        self, user_id: int, key_id: int, new_key: str
    ) -> BaseError | None:
        with DBManager.get_session() as session:
            return user_service.change_provider_key(session, user_id, key_id, new_key)

    def check_api_key_availability(self, api_key: str) -> ApiKey | BaseError:
        with DBManager.get_session() as session:
            return user_service.check_api_key_availability(session, api_key)

    def get_user_provider_keys(self, user_id: int) -> list[ProviderKey]:
        with DBManager.get_session() as session:
            return user_service.get_user_provider_keys(session, user_id)

    def get_user_api_keys(self, user_id: int) -> list[ApiKey]:
        with DBManager.get_session() as session:
            return user_service.get_user_api_keys(session, user_id)

    def revoke_api_key(self, key_id: int):
        with DBManager.get_session() as session:
            return user_service.revoke_api_key(session, key_id)

    def get_similiar_artists(
        self, id: int, count: int = 5
    ) -> list[ShortArtistResponse] | BaseError:
        artists = ScrobblersManager.get_similiar_artists(id, count)
        if isinstance(artists, BaseError):
            return artists
        return [to_short_artist_response(artist) for artist in artists]

    def get_album_by_id(self, id: int) -> FullAlbumResponse | BaseError:
        with DBManager.get_session() as session:
            album = album_service.get_album_by_id(session, id)
            return check_error(album, to_full_album_response)

    def get_artist_by_id(self, id: int) -> FullArtistResponse | BaseError:
        with DBManager.get_session() as session:
            artist = artist_service.get_artist_by_id(session, id)
            return check_error(artist, to_full_artist_response)

    def get_artist_top_tracks(self, name: str, count: int) -> list[ShortTrackResponse]:
        with DBManager.get_session() as session:
            tracks = artist_service.get_artist_top_songs(session, name, count)
            return [to_short_track_response(track) for track in tracks]

    def get_cover_art(self, id: int) -> BinaryBlob | BaseError:
        with DBManager.get_session() as session:
            return StoragesManager.get_cover_art(session, id)

    def get_genres(self) -> list[dict[str, str | int]]:
        with DBManager.get_session() as session:
            return track_service.get_genres(session)

    def get_moods(self) -> list[dict[str, str | int]]:
        with DBManager.get_session() as session:
            return track_service.get_moods(session)

    def get_playlist_by_id(self, id: int) -> FullPlaylistResponse | BaseError:
        with DBManager.get_session() as session:
            playlist = playlist_service.get_playlist_by_id(session, id)
            return check_error(playlist, to_full_playlist_response)

    def delete_user_by_username(self, username: str, user_id: int) -> int | BaseError:
        with DBManager.get_session() as session:
            return user_service.delete_user_by_username(session, username, user_id)

    def delete_user_by_id(self, id: int, user_id: int) -> int | BaseError:
        with DBManager.get_session() as session:
            return user_service.delete_user_by_id(session, id, user_id)

    # def delete_track(self, track_id: int):

    def star(self, user_id: int, object_id: int, object_type: str) -> BaseError | None:
        with DBManager.get_session() as session:
            return user_service.star(session, user_id, object_id, object_type)

    def unstar(
        self, user_id: int, object_id: int, object_type: str
    ) -> BaseError | None:
        with DBManager.get_session() as session:
            return user_service.unstar(session, user_id, object_id, object_type)

    def get_user_playlists(
        self, user_id: int, size: int = 10, offset: int = 0
    ) -> list[ShortPlaylistResponse]:
        with DBManager.get_session() as session:
            playlists = user_service.get_user_playlists(session, user_id, size, offset)
            return [to_short_playlist_response(playlist) for playlist in playlists]

    def create_playlist(
        self,
        user_id: int,
        title: str,
        tracks_id: list[int],
        is_public: bool = False,
        cover_path: int | None = None,
    ) -> FullPlaylistResponse | BaseError:
        with DBManager.get_session() as session:
            playlist = playlist_service.create_playlist(
                session, user_id, title, tracks_id, is_public, cover_path
            )
            return check_error(playlist, to_full_playlist_response)

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
        with DBManager.get_session() as session:
            user = user_service.update_user_by_username(
                session,
                acting_user_id,
                current_username,
                new_username,
                new_password,
                set_is_admin,
            )
            return check_error(user, to_short_user_response)

    def update_user_by_id(
        self,
        acting_user_id: int,
        changed_user_id: int,
        new_username: str | None = None,
        new_password: str | None = None,
        set_is_admin: bool | None = None,
    ) -> ShortUserResponse | BaseError:
        with DBManager.get_session() as session:
            user = user_service.update_user_by_id(
                session,
                acting_user_id,
                changed_user_id,
                new_username,
                new_password,
                set_is_admin,
            )
            return check_error(user, to_short_user_response)

    def create_user(
        self, username: str, email: str, password: str
    ) -> ShortUserResponse:
        with DBManager.get_session() as session:
            user = user_service.create_user(session, username, email, password)
            session.commit()
            return to_short_user_response(user)

    def delete_playlist(self, playlist_id: int):
        with DBManager.get_session() as session:
            return playlist_service.delete_playlist(session, playlist_id)

    def update_playlist(
        self,
        playlist_id: int,
        user_id: int,
        title: str | None = None,
        track_ids: list[int] | None = None,
        owner_ids: list[int] | None = None,
        is_public: bool | None = None,
    ) -> FullPlaylistResponse | BaseError:
        with DBManager.get_session() as session:
            playlist = playlist_service.update_playlist(
                session, playlist_id, user_id, title, track_ids, owner_ids, is_public
            )
            return check_error(playlist, to_full_playlist_response)

    def get_all_user_starred(
        self, user_id: int
    ) -> (
        tuple[
            list[ShortTrackResponse],
            list[ShortAlbumResponse],
            list[ShortArtistResponse],
        ]
        | BaseError
    ):
        with DBManager.get_session() as session:
            starred = user_service.get_all_user_starred(session, user_id)
            if isinstance(starred, BaseError):
                return starred
            tracks, albums, artists = starred
            return (
                [to_short_track_response(track) for track in tracks],
                [to_short_album_response(track) for track in albums],
                [to_short_artist_response(track) for track in artists],
            )

    def get_track_by_title(self, title: str) -> FullTrackResponse | BaseError:
        with DBManager.get_session() as session:
            track = track_service.get_track_by_title(session, title)
            return check_error(track, to_full_track_response)

    def get_lyrics(self, track_id: int) -> list[LyricsResponse] | BaseError:
        with DBManager.get_session() as session:
            return track_service.get_lyrics(session, track_id)

    def get_internal_user(
        self, username: str | None = None, user_id: int | None = None
    ) -> StoredUser | None | BaseError:
        with DBManager.get_session() as session:
            user = user_service.get_user(session, username, user_id)
            return user

    def get_user(
        self, username: str | None = None, user_id: int | None = None
    ) -> ShortUserResponse | None | BaseError:
        with DBManager.get_session() as session:
            user = user_service.get_user(session, username, user_id)
            if user is None or isinstance(user, BaseError):
                return user
            return to_short_user_response(user)

    def check_user_login(
        self, password: str, username: str | None = None, user_id: int | None = None
    ) -> BaseError | ShortUserResponse:
        with DBManager.get_session() as session:
            user = user_service.get_user(session, username, user_id)
            if user is None or isinstance(user, BaseError):
                return UnauthorizedError(detail="wrong username or password")
            if user.password != password:
                return UnauthorizedError(detail="wrong username or password")
            return to_short_user_response(user)

    def stream_track(
        self, id: str, start_bytes: int, end_bytes: int
    ) -> Iterator[bytes] | BaseError:
        return StoragesManager.stream_track(id, start_bytes, end_bytes)

    def get_albums_cursor(
        self, cursor: str | None, limit: int = 20
    ) -> tuple[list[ShortAlbumResponse], str | None]:
        with DBManager.get_session() as session:
            albums, cursor = album_service.get_albums_cursor(session, cursor, limit)
            return [to_short_album_response(album) for album in albums], cursor

    def get_artists_cursor(
        self, cursor: str | None, limit: int = 20
    ) -> tuple[list[ShortArtistResponse], str | None]:
        with DBManager.get_session() as session:
            artists, cursor = artist_service.get_artists_cursor(session, cursor, limit)
            return [to_short_artist_response(artist) for artist in artists], cursor

    def get_tracks_cursor(
        self, cursor: str | None, limit: int = 20
    ) -> tuple[list[ShortTrackResponse], str | None]:
        with DBManager.get_session() as session:
            tracks, cursor = track_service.get_tracks_cursor(session, cursor, limit)
            return [to_short_track_response(track) for track in tracks], cursor

    def get_file_metadata(self, id: str) -> FileMetadata | BaseError:
        return StoragesManager.get_file_metadata(id)

    def get_sync_task(self, task_id: str) -> Task[SyncTaskResult] | BaseError:
        return TasksManager.get_task("sync", task_id)

    def get_sync_tasks(self) -> dict[str, Task[SyncTaskResult]]:
        return TasksManager.get_tasks("sync")

    def cancel_sync_task(self, task_id: str) -> bool | BaseError:
        return TasksManager.cancel_task("sync", task_id)

    def get_download_task(self, task_id: str) -> Task[DownloadTaskResult] | BaseError:
        return TasksManager.get_task("download", task_id)

    def get_download_tasks(self) -> dict[str, Task[DownloadTaskResult]]:
        return TasksManager.get_tasks("download")

    def cancel_download_task(self, task_id: str) -> bool | BaseError:
        return TasksManager.cancel_task("download", task_id)

    def get_import_task(self, task_id: str) -> Task[ImportTaskResult] | BaseError:
        return TasksManager.get_task("importing", task_id)

    def get_import_tasks(self) -> dict[str, Task[ImportTaskResult]]:
        return TasksManager.get_tasks("importing")

    def cancel_import_task(self, task_id: str) -> bool | BaseError:
        return TasksManager.cancel_task("importing", task_id)

    def sync(self, task_id: str | None = None) -> str:
        task_id = TasksManager.post_task(
            StoragesManager.sync_library,
            task_id=task_id,
            queue_name="sync",
            task_result=SyncTaskResult(),
        )
        return task_id

    def import_library(
        self,
        task_id: str | None = None,
        importer_tag: str | None = None,
        user_id: int | None = None,
    ) -> str:
        task_id = TasksManager.post_task(
            func=ImportersManager.import_tracks,
            queue_name="importing",
            task_id=task_id,
            importer_tag=importer_tag,
            user_id=user_id,
            task_result=ImportTaskResult(),
        )
        return task_id

    def get_all_users(self) -> list[ShortUserResponse]:
        with DBManager.get_session() as session:
            users = user_service.get_all_users(session)
            return [to_short_user_response(user) for user in users]

    def check_status(self) -> ServicesStatus:
        return server_service.check_status()

    def get_library_stats(self) -> LibraryStats:
        with DBManager.get_session() as session:
            return server_service.get_library_stats(session)
