from pathlib import Path
import tomllib

from search.base import Search as BaseSearch
from downloader.base import Downloader as BaseDownloader
from storage.base import Storage as BaseStorage
from .schemas import QueryType
from utils.utils import compare_tracks, find_best_track
import shutil
from .db.models import DBManager, Track, TrackLink, Album, Artist
import mutagen
import time
import os
from core.loader import import_modules, load_storages, load_modules
from typing import Callable


class LibraryManager:

    def __init__(self) -> None:
        path = Path(__file__).resolve()
        config_path = path.parents[1] / "config.toml"
        with config_path.open("rb") as config_file:
            config = tomllib.load(config_file)
        self.config = config

        self.search_engines = load_modules(
            config["search"], import_modules("search", BaseSearch)
        )
        self.storages = load_storages(config, import_modules("storage", BaseStorage))
        self.downloaders = load_modules(
            config["downloader"], import_modules("downloader", BaseDownloader)
        )
        self.db_manager = DBManager()

    def search(self, query: str, media_type: QueryType):
        search_results = []
        for engine in self.search_engines:
            search_engine = engine["class"](engine["params"])
            if media_type == QueryType.TRACK or media_type == QueryType.ALL:
                res = search_engine.search_tracks(query)
                if res:
                    search_results.extend(res)
            if media_type == QueryType.ALBUM or media_type == QueryType.ALL:
                res = search_engine.search_albums(query)
                if res:
                    search_results.extend(res)
            if media_type == QueryType.ARTIST or media_type == QueryType.ALL:
                res = search_engine.search_artists(query)
                if res:
                    search_results.extend(res)
        return search_results

    def download(self, query: str, progress_callback: Callable[[int], None]):
        downloaders = self.downloaders

        search_results = []
        tracks_dict = []
        searched_tracks = []
        best_storage = None

        for engine in self.search_engines:
            search_engine = engine["class"](engine["params"])
            results = search_engine.search_tracks(query)
            for track in results:
                track["searched_by"] = search_engine.TAG
                search_results.append(track)

        for downloader in downloaders:
            current_downloader = downloader["class"](downloader["params"])
            downloader_search = current_downloader.search(query)
            for file in downloader_search:
                file["downloader"] = current_downloader.TAG
                searched_tracks.append(file)

        original_track = find_best_track(search_results)

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
            (d for d in downloaders if d["tag"] == best_track["downloader"]), None
        )
        downloader = track_downloader["class"](
            self.config["downloader"][best_track["downloader"]]["params"]
        )
        track_path = downloader.download(best_track, progress_callback)
        downloaded_path = Path(track_path)

        for storage in self.storages:
            params = storage["params"].copy()
            params.update({"id": storage["id"], "name": storage["name"]})
            current_storage = storage["class"](params)
            free_storage = current_storage.check_storage()
            if free_storage > best_track["size"]:
                best_storage = current_storage
                break

        dst = Path("temp_tracks") / downloaded_path.name

        if downloaded_path.exists():
            shutil.copy2(downloaded_path, dst)
            track_metadata = mutagen.File(dst, easy=True)
            title = (track_metadata.get("title") or [downloaded_path.stem])[0]
            artist_name = (track_metadata.get("artist") or ["Unknown"])[0]
            album_title = (track_metadata.get("album") or [None])[0]
            bpm = getattr(track_metadata.info, "bpm", None)
            bitrate = getattr(track_metadata.info, "bitrate", None)
            length = int(getattr(track_metadata.info, "length", 0))
            saving_path = Path(
                (f"{artist_name}/{album_title}/{dst.name}").replace(" ", "-")
            )
            saved_path = best_storage.save_track(dst, saving_path)
            with self.db_manager.get_session() as session:
                db_artist = self.db_manager.get_artist_by_name(session, artist_name)
                if db_artist is None:
                    db_artist = self.db_manager.add(session, Artist(name=artist_name))

                if album_title:
                    db_album = self.db_manager.get_album_by_name(session, album_title)
                    if db_album is None:
                        db_album = Album(title=album_title)
                        db_artist.albums.append(db_album)
                        session.flush()
                else:
                    db_album = None

                new_track = Track(title=title, length=length, album=db_album)
                new_link = TrackLink(
                    link_type="storage",
                    link_provider=best_storage.id,
                    link=str(saved_path),
                )
                new_track.links.append(new_link)
                session.add(new_track)

                session.commit()
            # for i in range(5):
            #    try:
            #        os.remove(downloaded_path)
            #        break
            #    except PermissionError:
            #        print(f"File locked(attempt {i+1}/5)")
            #        time.sleep(4)
            return {
                "title": title,
                "artist": [artist_name],
                "length": length,
                "storage": best_storage.name,
                "download_source": downloader.TAG,
                "saved_path": saved_path,
            }

    def get_all_tracks(self):
        tracks = self.db_manager.get_all_tracks()
        return tracks

    def delete_track(self, track_id: int):
        track = self.db_manager.delete_track(track_id)
        return track

    def import_tracks():
        pass

    def stream_track(self, track_id: int, start_bytes: int, end_bytes: int):
        track = self.db_manager.get_track_by_id(track_id)
        track_storage = next(
            (links for links in track.links if links.link_type == "storage"), None
        )
        for storage in self.storages:
            params = storage["params"].copy()
            params.update({"id": storage["id"], "name": storage["name"]})
            current_storage = storage["class"](params)
            if current_storage.id == track_storage.link_provider:
                track = current_storage.stream_track(
                    track_storage.link, start_bytes, end_bytes
                )
                print(track)
                return track

    def sync(self):
        with self.db_manager.get_session() as session:
            db_tracks = self.db_manager.get_all_tracks_storage_links()
            storaged_tracks = set()
            for storage in self.storages:
                params = storage["params"].copy()
                params.update({"id": storage["id"], "name": storage["name"]})
                current_storage = storage["class"](params)
                tracks_path = current_storage.get_all_tracks_paths()
                named_paths = [f"{storage["id"]}///{f}" for f in tracks_path]
                storaged_tracks.update(named_paths)
            deleted_tracks_links = db_tracks - storaged_tracks
            added_tracks_links = storaged_tracks - db_tracks
            tracks_for_deleting = [
                (track.split("///")[0], track.split("///")[1])
                for track in deleted_tracks_links
            ]
            deleted_count = self.db_manager.bulk_delete_by_links(tracks_for_deleting)
            tracks_to_adding = {}
            for track in added_tracks_links:
                k, v = track.split("///")
                if k in tracks_to_adding:
                    tracks_to_adding[k].append(v)
                else:
                    tracks_to_adding[k] = [v]
            for storage in self.storages:
                params = storage["params"].copy()
                params.update({"id": storage["id"], "name": storage["name"]})
                current_storage = storage["class"](params)
                if storage["id"] in tracks_to_adding:
                    for path in tracks_to_adding[storage["id"]]:
                        track_metadata = current_storage.get_track_metadata(path)
                        new_track = Track(
                            title=track_metadata["title"],
                            artist=track_metadata["artist"],
                            length=track_metadata["length"],
                        )
                        new_link = TrackLink(
                            link_type="storage",
                            link_provider=current_storage.id,
                            link=str(path),
                        )
                        new_track.links.append(new_link)
                        self.db_manager.add(session, new_track)
            session.commit()

    def checks_status():
        pass
