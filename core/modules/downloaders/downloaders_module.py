import shutil
from pathlib import Path

from core.db.manager import DBManager
from core.db.models import ObjectStorageORM
from core.errors import BaseError
from core.modules import Module
from core.modules.downloaders.loader import load_downloaders
from core.modules.downloaders.utils import compare_tracks, find_best_track
from core.modules.searches.searches_module import SearchesModule
from core.modules.storages.storages_module import StoragesModule
from core.schemas import FilePathInfo, Track
from core.services import (
    track_service,
)
from core.tasks.schemas import DownloadTaskResult
from core.tasks.tasks_manager import TasksManager
from core.utils import full_track_save, get_track_metadata_by_path


class DownloadersModule(Module):
    ID = "downloader"

    def __init__(self, modules, config, logger):
        super().__init__(modules, config, logger)
        self.downloaders, self.statuses = load_downloaders(self.config)
        self.temp_dir = Path("temp_files")

    def download_track(
        self,
        task_id: str,
        query: str | None = None,
        object_id: str | None = None,
    ):
        search_module = self.modules.get(SearchesModule)
        storage_module = self.modules.get(StoragesModule)
        if isinstance(search_module, BaseError) or isinstance(
            storage_module, BaseError
        ):
            return
        if query is None and object_id is None:
            return
        downloaders = self.downloaders
        original_track: Track | None = None

        tracks_dict = []
        searched_tracks = []
        if query:
            search_results = search_module.global_search(query).tracks
            if len(search_results) < 1:
                return
            original_track = find_best_track(search_results)
        elif object_id:
            track = search_module.get_global_object("track", object_id)
            original_track = track
        if original_track is None:
            return
        search_query = original_track.title if object_id else query
        for downloader in downloaders:
            current_downloader = downloader.instance
            downloader_search = current_downloader.search(search_query)
            for file in downloader_search:
                file["downloader"] = current_downloader.TAG
                searched_tracks.append(file)
        for track in searched_tracks:
            similarity = compare_tracks(original_track, track)
            tracks_dict.append({"id": track["id"], "similarity": similarity})
        tracks = sorted(
            tracks_dict, key=lambda track: track["similarity"], reverse=True
        )
        best_track = next(
            (t for t in searched_tracks if t["id"] == tracks[0]["id"]), None
        )
        track_downloader = next(
            (d for d in downloaders if d.tag == best_track["downloader"]), None
        )
        downloader = track_downloader.instance
        track_path = downloader.download(
            best_track, lambda progress: self._update_progress(task_id, progress)
        )
        downloaded_path = Path(track_path)
        dst = self.temp_dir / downloaded_path.name

        if downloaded_path.exists():
            shutil.copy2(downloaded_path, dst)
            track = get_track_metadata_by_path(dst)
            title = track.title
            artist_name = track.artists[0]
            album_title = track.albums[0].title
            saving_path = Path(f"{artist_name}/{album_title}/{dst.name}")
            best_storage = storage_module.find_best_storage(
                file_size=best_track["size"]
            )
            paths = full_track_save(best_storage, dst, saving_path)
            cover_storage_path = paths["cover_path"]
            saved_path = paths["track_path"]
            with DBManager.get_session() as session:
                cover = ObjectStorageORM(
                    file_name=Path(cover_storage_path).name,
                    link_provider=best_storage.id,
                    link=cover_storage_path,
                )
                session.add(cover)
                session.flush(cover)
                track_service.add_new_track(
                    session,
                    track,
                    FilePathInfo(link=saved_path, filename=dst.name),
                    best_storage.id,
                    cover.id,
                )
                session.commit()
            TasksManager.task_queue.download[task_id].result = DownloadTaskResult(
                title=title,
                artist=track.artists,
                length=track.length,
                storage=best_storage.name,
                download_source=downloader.TAG,
                saved_path=saved_path,
            )
            TasksManager.task_queue.download[task_id].status = "finished"
