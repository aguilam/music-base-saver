import os
from collections import defaultdict
from collections.abc import Iterator
from pathlib import Path

from sqlmodel import Session

from core.db.manager import DBManager
from core.db.models import LyricsORM, MusicVideoORM, ObjectStorageORM
from core.errors import BaseError, NotFoundError
from core.loader import import_modules
from core.modules import Module
from core.modules.storages.base import Storage
from core.modules.storages.loader import StorageEntry, load_storages
from core.modules.storages.schemas import FileMetadata
from core.schemas import BinaryBlob, FilePathInfo, LRCLyrics
from core.services import (
    album_service,
    artist_service,
    playlist_service,
    server_service,
    track_service,
)
from core.tasks.schemas import SyncTaskResult, Task
from core.tasks.tasks_manager import TasksManager
from core.utils import (
    get_cover_metadata,
    get_id_from_string,
    get_track_metadata_by_bytes,
    get_video_metadata,
    image_mime,
    read_lyrics_text,
)


class StoragesModule(Module):
    ID = "storage"

    def __init__(self, modules, config, logger):
        super().__init__(modules, config, logger)
        self.temp_dir = Path("temp_files")
        self.config: list
        self.storages, self.statuses = load_storages(
            self.config, import_modules(__file__, Storage)
        )

    def get_cover_art(self, session: Session, id: int) -> BinaryBlob | BaseError:
        storage = server_service.get_storage_object_by_id(session, id)
        if storage is None:
            print("t1")
            return NotFoundError()
        cover_art = self.get_file(storage.link, storage.link_provider)
        if cover_art is None:
            return NotFoundError()
        cover_mime = image_mime(cover_art)
        return BinaryBlob(cover_art, cover_mime)

    def find_best_storage(self, file_size: int) -> StorageEntry | BaseError:
        for storage in self.storages:
            current_storage = storage.instance
            free_storage = current_storage.check_storage()
            if free_storage > file_size:
                return storage
            return BaseError(code=500, detail="No available storages")
        return BaseError(code=500, detail="No available storages")

    def stream_track(
        self, id: str, start_bytes: int, end_bytes: int
    ) -> Iterator[bytes] | BaseError:
        with DBManager.get_session() as session:
            object_id = None
            if "cl-" in id:
                video_id = id.split("-")[1]
                video = track_service.get_video_by_id(session, int(video_id))
                if isinstance(video, BaseError):
                    return video
                object_id = video.local_link
            else:
                track = track_service.get_track_by_id(session, int(id))
                if isinstance(track, BaseError):
                    return track
                object_id = track.path
            if object_id is None:
                return NotFoundError()
            storage_object = server_service.get_storage_object_by_id(session, object_id)
            if storage_object is None:
                return NotFoundError()
            media_storage = storage_object.link_provider
            media_link = storage_object.link
            for storage in self.storages:
                if storage.id == media_storage:
                    current_storage = storage.instance
                    track = current_storage.get_range_bytes(
                        media_link, start_bytes, end_bytes
                    )
                    return track
            return NotFoundError()

    def get_file_metadata(self, id: str) -> FileMetadata | BaseError:
        with DBManager.get_session() as session:
            object_id = None
            if "cl-" in id:
                video_id = id.split("-")[1]
                video = track_service.get_video_by_id(session, int(video_id))
                if isinstance(video, BaseError):
                    return video
                object_id = video.local_link
            else:
                track = track_service.get_track_by_id(session, int(id))
                if isinstance(track, BaseError):
                    return track
                object_id = track.path
            if object_id is None:
                return NotFoundError()
            storage = server_service.get_storage_object_by_id(session, object_id)
            if storage is None:
                return NotFoundError()
            media_storage = storage.link_provider
            media_link = storage.link
            for storage in self.storages:
                if storage.id == media_storage:
                    current_storage = storage.instance
                    metadata = current_storage.get_file_metadata(media_link)
                    return metadata
            return NotFoundError()

    def get_file(self, path: str, storage_id: str) -> bytes | None:
        for storage in self.storages:
            current_storage = storage.instance
            if current_storage.id == storage_id:
                cover_path = current_storage.get_file(path)
                return Path(cover_path).read_bytes()

    def save_object(
        self,
        session: Session,
        file_path: str,
        saving_path: str,
        file_size: int | None = None,
    ) -> ObjectStorageORM | BaseError:
        file_size = os.path.getsize(file_path) if file_size is None else file_size
        best_storage = self.find_best_storage(file_size)
        if isinstance(best_storage, BaseError):
            return best_storage
        saved_object_path = best_storage.instance.save_file(file_path, saving_path)
        object_storage = ObjectStorageORM(
            link_provider=best_storage.id,
            file_name=os.path.basename(saving_path),
            link=saved_object_path,
        )
        session.add(object_storage)
        session.flush()
        return object_storage

    def sync_library(self, task_id: str):
        try:
            task: Task[SyncTaskResult] | BaseError = TasksManager.get_task(
                "sync", task_id
            )
            if isinstance(task, BaseError):
                TasksManager.cancel_task("sync", task_id)
                return
            with DBManager.get_session() as session:
                db_files = track_service.get_all_tracks_storage_links(session)
                storaged_files: set[tuple[str, str]] = set()
                if len(self.storages) == 0:
                    task.status = "error"
                    task.error = "No connected storages"
                    TasksManager.cancel_task("sync", task_id)
                for storage in self.storages:
                    current_storage = storage.instance
                    tracks_path = current_storage.get_all_files_paths()
                    named_paths = [
                        (f"{storage.id}///{link}", file_name)
                        for link, file_name in tracks_path
                    ]
                    storaged_files.update(named_paths)
                deleted_objects_links = db_files - storaged_files
                added_object_links = storaged_files - db_files
                objects_for_deleting = [
                    (track.split("///")[0], track.split("///")[1])
                    for track, _ in deleted_objects_links
                ]
                deleted_tracks, deleted_covers, deleted_lyrics, deleted_videos = (
                    server_service.bulk_delete_by_links(session, objects_for_deleting)
                )
                task.result.tracks.deleted = deleted_tracks
                task.result.covers.deleted = deleted_covers
                task.result.lyrics.deleted = deleted_lyrics
                task.result.videos.deleted = deleted_videos
                tracks_to_adding: defaultdict[str, list[FilePathInfo]] = defaultdict(
                    list
                )
                cover_to_adding: defaultdict[str, list[FilePathInfo]] = defaultdict(
                    list
                )
                lyrics_to_adding: defaultdict[str, list[FilePathInfo]] = defaultdict(
                    list
                )
                videos_to_adding: defaultdict[str, list[FilePathInfo]] = defaultdict(
                    list
                )
                for link, file_name in added_object_links:
                    k, v = link.split("///", 1)
                    file_info = FilePathInfo(link=v, filename=file_name)
                    if any(ext in v for ext in ["jpeg", "jpg", "png"]):
                        cover_to_adding[k].append(file_info)
                        task.result.covers.searched_new += 1
                    elif any(ext in v for ext in ["lrc", "txt"]):
                        lyrics_to_adding[k].append(file_info)
                        task.result.lyrics.searched_new += 1
                    elif "mp4" in v:
                        videos_to_adding[k].append(file_info)
                        task.result.videos.searched_new += 1
                    elif any(ext in v for ext in ["m4a", "flac", "mp3", "opus"]):
                        tracks_to_adding[k].append(file_info)
                        task.result.tracks.searched_new += 1
                for storage in self.storages:
                    current_storage = storage.instance
                    for track in tracks_to_adding.get(storage.id, []):
                        try:
                            track_bytes = b"".join(
                                current_storage.get_range_bytes(
                                    track.link, 0, 1024 * 1024 * 5
                                )
                            )
                            track_metadata = get_track_metadata_by_bytes(track_bytes)
                            track_service.add_new_track(
                                session, track_metadata, track, storage.id
                            )
                            session.commit()
                            task.result.tracks.added += 1
                        except Exception:
                            session.rollback()
                            continue
                        finally:
                            task.result.tracks.processed += 1
                    for cover in cover_to_adding.get(storage.id, []):
                        try:
                            cover_link, cover_name = cover
                            entity = None
                            range_bytes: bytes = b"".join(
                                current_storage.get_range_bytes(cover_link, 0, 99999999)
                            )
                            cover_metadata = get_cover_metadata(
                                range_bytes,
                            )
                            if cover_metadata:
                                title = cover_metadata.get("title")
                                artists = cover_metadata.get("creator")
                                if title:
                                    entity = album_service.get_album_orm_by_title(
                                        session, title
                                    )
                                elif artists and len(artists) == 1:
                                    entity = artist_service.get_artist_orm_by_name(
                                        session, artists[0]
                                    )
                            id_tuple = get_id_from_string(cover_name)
                            if id_tuple and not entity:
                                content_type, content_id = id_tuple
                                if content_type == "al":
                                    entity = album_service.get_album_orm_by_id(
                                        session, content_id
                                    )
                                elif content_type == "ar":
                                    entity = artist_service.get_artist_orm_by_id(
                                        session, content_id
                                    )
                                elif content_type == "pl":
                                    entity = playlist_service.get_playlist_orm_by_id(
                                        session, content_id
                                    )
                            if entity is None:
                                task.result.unbound_files.covers.add(
                                    (f"{storage.id}///{cover_link}", cover_name)
                                )
                                task.result.covers.processed += 1
                                continue
                            cover_storage = ObjectStorageORM(
                                link_provider=storage.id,
                                link=cover_link,
                                file_name=cover_name,
                            )
                            session.add(cover_storage)
                            session.flush()
                            entity.cover_path = cover_storage.id
                            session.commit()
                            task.result.covers.added += 1
                        except Exception:
                            session.rollback()
                            continue
                        finally:
                            task.result.covers.processed += 1
                    for lyrics in lyrics_to_adding.get(storage.id, []):
                        try:
                            link, filename = lyrics
                            range_bytes: bytes = b"".join(
                                current_storage.get_range_bytes(lyrics.link, 0, 9999999)
                            )
                            decoded_text = range_bytes.decode()
                            lyrics_text = read_lyrics_text(decoded_text)
                            name = filename.split(".")[0]
                            if isinstance(lyrics_text, LRCLyrics):
                                track = track_service.get_track_by_title(
                                    session, lyrics_text.title
                                )
                                if isinstance(track, NotFoundError):
                                    track = track_service.get_track_by_title(
                                        session, name
                                    )
                                if isinstance(track, BaseError):
                                    task.result.unbound_files.lyrics.add(
                                        (f"{storage.id}///{link}", filename)
                                    )
                                    task.result.lyrics.processed += 1
                                    continue
                                new_lyrics = LyricsORM(
                                    is_synced=True,
                                    language="und",
                                    synced_text=lyrics_text.text,
                                    offset=lyrics_text.offset,
                                    track_id=track.id,
                                )
                                session.add(new_lyrics)
                                session.flush()
                            elif isinstance(lyrics_text, str):
                                track = track_service.get_track_by_title(session, name)
                                if isinstance(track, BaseError):
                                    task.result.unbound_files.lyrics.add(
                                        (f"{storage.id}///{link}", filename)
                                    )
                                    task.result.lyrics.processed += 1
                                    continue
                                new_lyrics = LyricsORM(
                                    is_synced=False,
                                    language="und",
                                    plain_text=lyrics_text,
                                    track_id=track.id,
                                )
                                session.add(new_lyrics)
                                session.flush()
                            lyrics_path = ObjectStorageORM(
                                link_provider=storage.id,
                                link=link,
                                lyrics_id=new_lyrics.id,
                                file_name=filename,
                            )
                            new_lyrics.path.append(lyrics_path)
                            session.add(lyrics_path)
                            session.commit()
                            task.result.lyrics.added += 1
                        except Exception:
                            session.rollback()
                            continue
                        finally:
                            task.result.lyrics.processed += 1
                    for video in videos_to_adding.get(storage.id, []):
                        try:
                            link, filename = video
                            video_bytes = b"".join(
                                current_storage.get_range_bytes(
                                    video.link, 0, 1024 * 1024 * 5
                                )
                            )
                            video_metadata = get_video_metadata(video_bytes)
                            video_title = video_metadata.get("title")
                            if video_title is None:
                                video_title = filename.rsplit(".", 1)[0]
                            track = track_service.get_track_by_title(
                                session, video_title
                            )
                            if isinstance(track, NotFoundError):
                                id_tuple = get_id_from_string(filename, "tr")
                                if id_tuple:
                                    track = track_service.get_track_by_id(
                                        session, id_tuple[1]
                                    )
                            if isinstance(track, BaseError):
                                task.result.unbound_files.videos.add(
                                    (f"{storage.id}///{link}", filename)
                                )
                                task.result.videos.processed += 1
                                continue
                            music_video = MusicVideoORM(
                                is_external_link=False,
                                track_id=track.id,
                            )
                            session.add(music_video)
                            session.flush()
                            video_storage = ObjectStorageORM(
                                link_provider=storage.id,
                                link=link,
                                file_name=filename,
                            )
                            music_video.local_link.append(video_storage)
                            session.add(music_video)
                            session.flush()
                            task.result.videos.added += 1
                        except Exception:
                            session.rollback()
                            continue
                        finally:
                            task.result.videos.processed += 1

                server_service.delete_orphans(session)
                session.commit()
                TasksManager.task_queue.sync[task_id].status = "finished"
                self.logger.info("Syncing succesful completed")
        except Exception as e:
            TasksManager.task_queue.sync[task_id].status = "error"
            TasksManager.task_queue.sync[task_id].error = str(e)
            self.logger.warning(
                "Problem in library syncing", task_id=task_id, error=str(e)
            )
