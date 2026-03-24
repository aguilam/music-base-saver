from pathlib import Path
import tomllib
from search.base import Search as BaseSearch
from downloader.base import Downloader as BaseDownloader
from storage.base import Storage as BaseStorage
from importer.base import Importer as BaseImporter
from .schemas import QueryType
from utils.utils import compare_tracks, find_best_track, get_cover
import shutil
from .db.models import (
    DBManager,
    Track,
    TrackLink,
    Album,
    Artist,
    StarredAlbum,
    StarredArtist,
    StarredTrack,
    Playlist,
    User,
)
import mutagen
from sqlalchemy import select
from core.loader import import_modules, load_storages, load_modules
from typing import Callable

STAR_LINK_MAP = {
    "track": lambda user_id, obj_id: StarredTrack(user_id=user_id, track_id=obj_id),
    "album": lambda user_id, obj_id: StarredAlbum(user_id=user_id, album_id=obj_id),
    "artist": lambda user_id, obj_id: StarredArtist(user_id=user_id, artist_id=obj_id),
}

UNSTAR_LINK_MAP = {
    "track": (StarredTrack, "song_id"),
    "album": (StarredAlbum, "album_id"),
    "artist": (StarredArtist, "artist_id"),
}


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
        self.importers = load_modules(
            config["importer"], import_modules("importer", BaseImporter)
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
            cover = get_cover(dst)
            if cover is not None:
                bytes, ext = cover
                cover_path = dst.parent / f"cover.{ext}"
                cover_path.write_bytes(bytes)
                cover_save_path = saving_path.parent / cover_path.name
                cover_storage_path = best_storage.save_track(
                    cover_path, cover_save_path
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
                    if db_album.cover_path is None and cover is not None:
                        db_album.cover_path = (
                            f"{best_storage.id}///{cover_storage_path}"
                        )
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
            return {
                "title": title,
                "artist": [artist_name],
                "length": length,
                "storage": best_storage.name,
                "download_source": downloader.TAG,
                "saved_path": saved_path,
            }

    def get_file(self, path: str, storage_id: str):
        for storage in self.storages:
            params = storage["params"].copy()
            params.update({"id": storage["id"], "name": storage["name"]})
            current_storage = storage["class"](params)
            if current_storage.id == storage_id:
                cover_path = current_storage.get_track(path)
                return Path(cover_path).read_bytes()

    def get_all_tracks(self):
        tracks = self.db_manager.get_all_tracks()
        return tracks

    def get_all_artists(self):
        artists = self.db_manager.get_all_artists()
        return artists

    def get_all_albums(self):
        albums = self.db_manager.get_all_albums()
        return albums

    def get_track_by_id(self, id: int):
        track = self.db_manager.get_track_by_id(id)
        return track

    def get_album_by_id(self, id: int):
        with self.db_manager.get_session() as session:
            album = self.db_manager.get_album_by_id(session, id)
            return album

    def get_artist_by_id(self, id: int):
        with self.db_manager.get_session() as session:
            artist = self.db_manager.get_artist_by_id(session, id)
            return artist

    def get_playlist_by_id(self, id: int):
        with self.db_manager.get_session() as session:
            playlist = self.db_manager.get_playlist_by_id(session, id)
            if playlist is None:
                return None
            if playlist:
                session.expunge_all()
            return playlist

    def delete_track(self, track_id: int):
        track = self.db_manager.delete_track(track_id)
        return track

    def star(self, user_id: int, object_id: int, object_type: str):
        factory = STAR_LINK_MAP.get(object_type)
        if not factory:
            raise ValueError(f"Unknown type: {object_type}")

        link = factory(user_id, object_id)

        with self.db_manager.get_session() as session:
            session.add(link)
            session.commit()

    def unstar(self, user_id: int, object_id: int, object_type: str):
        model, id_field = UNSTAR_LINK_MAP.get(object_type)
        if not model:
            raise ValueError(f"Unknown type: {object_type}")

        with self.db_manager.get_session() as session:
            statement = select(model).where(
                model.user_id == user_id,
                getattr(model, id_field) == object_id,
            )
            link = session.exec(statement).first()
            if link:
                session.delete(link)
                session.commit()

    def get_user_playlists(self, user_id: int) -> list[Playlist]:
        with self.db_manager.get_session() as session:
            return self.db_manager.get_user_playlists(session, user_id)

    def get_all_albums(self) -> list[Album]:
        with self.db_manager.get_session() as session:
            return self.db_manager.get_all_albums(session)

    def get_all_user_starred(self, user_id: int):
        return self.db_manager.get_all_user_starred(
            self.db_manager.get_session(), user_id
        )

    def get_user(
        self, username: str | None = None, apiKey: str | None = None
    ) -> User | None:
        with self.db_manager.get_session() as session:
            if username is not None:
                return self.db_manager.get_user_by_name(session, username)
            elif apiKey is not None:
                return self.db_manager.get_user_by_apikey(session, apiKey)
            else:
                return None

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
            cover_to_adding = {}
            track_added_count = 0
            cover_added_count = 0
            for track in added_tracks_links:
                k, v = track.split("///")
                if any(ext in v for ext in ["jpeg", "jpg", "png"]):
                    if k in cover_to_adding:
                        cover_to_adding[k].append(v)
                    else:
                        cover_to_adding[k] = [v]
                else:
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
                        db_artist = self.db_manager.get_artist_by_name(
                            session, track_metadata["artist"]
                        )
                        if db_artist is None:
                            db_artist = self.db_manager.add(
                                session, Artist(name=track_metadata["artist"])
                            )

                        if track_metadata["album"]:
                            db_album = self.db_manager.get_album_by_name(
                                session, track_metadata["album"]
                            )
                            if db_album is None:
                                db_album = Album(title=track_metadata["album"])
                                db_artist.albums.append(db_album)
                                session.flush()
                        else:
                            db_album = None

                        new_track = Track(
                            title=track_metadata["title"],
                            length=track_metadata["length"],
                            album=db_album,
                        )
                        new_link = TrackLink(
                            link_type="storage",
                            link_provider=current_storage.id,
                            link=str(path),
                        )
                        new_track.links.append(new_link)
                        session.add(new_track)
                        session.flush()
                        track_added_count += 1
                if storage["id"] in cover_to_adding:
                    for path in cover_to_adding[storage["id"]]:
                        content_id = None
                        content_type = None
                        entity = None
                        id_from_cover = current_storage.get_cover_metadata(path)
                        if id_from_cover is None:
                            file_name = Path(path).stem.split(":")[1]
                            subject, subject_id = file_name.split("-")
                            subject_id = int(subject_id)
                            if subject == "al":
                                album = self.db_manager.get_album_by_id(
                                    session, subject_id
                                )
                                if album is None:
                                    continue
                                content_type = "al"
                                content_id = album.id
                            elif subject == "ar":
                                artist = self.db_manager.get_artist_by_id(
                                    session, subject_id
                                )
                                if artist is None:
                                    continue
                                content_type = "ar"
                                content_id = artist.id
                            elif subject == "pl":
                                playlist = self.db_manager.get_playlist_by_id(
                                    session, subject_id
                                )
                                if playlist is None:
                                    continue
                                content_type = "pl"
                                content_id = playlist.id
                            current_storage.write_cover_metadata(
                                path, f"{content_type}-{content_id}"
                            )
                        else:
                            subject, subject_id = id_from_cover.split("-")
                            content_type = subject
                            content_id = int(subject_id)
                        if content_id is None or content_type is None:
                            continue
                        if content_type == "al":
                            entity = self.db_manager.get_album_by_id(
                                session, content_id
                            )
                        elif content_type == "ar":
                            entity = self.db_manager.get_artist_by_id(
                                session, content_id
                            )
                        elif content_type == "pl":
                            entity = self.db_manager.get_playlist_by_id(
                                session, content_id
                            )
                        if entity is None:
                            return
                        entity.cover_path = f"{storage["id"]}///{path}"
                        session.flush()
                        cover_added_count += 1
            session.commit()
            return {
                "deleted_count": deleted_count,
                "added_count": track_added_count + cover_added_count,
            }

    def import_tracks(self, importer_tag: str, user_id: int | None = None):
        importers = self.importers
        selected_importer: BaseImporter | None = None
        for importer in importers:
            if importer["tag"] == importer_tag:
                selected_importer = importer["class"](importer["params"])
                break
        with self.db_manager.get_session() as session:
            (
                favorited_tracks,
                favorited_albums,
                favorited_artists,
                favorited_playlists,
            ) = selected_importer.get_favorited()
            unique_tracks = {track["id"]: {} for track in favorited_tracks}
            unique_albums = {album["id"]: {} for album in favorited_albums}
            unique_artists = {artist["id"]: {} for artist in favorited_artists}
            unique_playlists = {playlist["id"]: {} for playlist in favorited_playlists}

            unique_playlists.update(
                playlist["id"] for playlist in selected_importer.get_playlists()
            )

            for playlist in unique_playlists:
                playlist_info = selected_importer.get_playlist(playlist["id"])
                for track in playlist_info["tracks"]:
                    unique_tracks[track["id"]] = track
                playlist_cover = selected_importer.get_playlist_cover()

            for track in unique_tracks:
                try:
                    track_info = selected_importer.get_tracks(track["id"])

                    track_path = selected_importer.get_track_download(track["id"])

                    for album in playlist_info["albums"]:
                        unique_albums[album["id"]] = album
                    for artist in playlist_info["artists"]:
                        unique_artists[artist["id"]] = artist
                except:
                    pass
            track_lyrics = selected_importer.get_lyrics()

    def checks_status():
        pass
