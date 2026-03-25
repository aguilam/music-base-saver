from pathlib import Path
import tomllib
from search.base import Search as BaseSearch
from downloader.base import Downloader as BaseDownloader
from storage.base import Storage as BaseStorage
from importer.base import Importer as BaseImporter
from .schemas import QueryType
from utils.utils import (
    compare_tracks,
    find_best_track,
    full_track_save,
    find_best_storage,
    analyze_track,
    save_url_file,
)
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
    TrackArtistsLink,
    Lyrics,
    PlaylistTrackLink,
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

        dst = Path("temp_tracks") / downloaded_path.name

        if downloaded_path.exists():
            shutil.copy2(downloaded_path, dst)
            track = analyze_track(dst, downloaded_path.stem)
            title = track["title"]
            artist_name = track["artist_name"]
            album_title = track["album_title"]
            length = track["length"]
            saving_path = Path(
                (f"{artist_name}/{album_title}/{dst.name}").replace(" ", "-")
            )
            best_storage = find_best_storage(self.storages, best_track["size"])
            paths = full_track_save(best_storage, dst, saving_path)
            cover_storage_path = paths["cover_path"]
            saved_path = paths["track_path"]
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
                    if db_album.cover_path is None and cover_storage_path is not None:
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
            user_id = 1 if user_id is None else user_id
            unique_tracks = {
                track["id"]: {"id": track["id"]} for track in favorited_tracks
            }
            unique_albums = {
                album["id"]: {"id": album["id"]} for album in favorited_albums
            }
            unique_artists = {
                artist["id"]: {"id": artist["id"]} for artist in favorited_artists
            }
            unique_playlists = {
                playlist["id"]: {"id": playlist["id"]}
                for playlist in favorited_playlists
            }
            favorited_tracks = favorited_tracks[:10]
            favorited_albums = favorited_albums[:5]
            favorited_artists = favorited_artists[:5]
            favorited_playlists = favorited_playlists[:3]
            playlists_to_add = []
            tracks_to_add = []
            artist_map: dict[int, int] = {}
            album_map: dict[int, int] = {}
            track_map: dict[int, int] = {}

            unique_playlists.update(
                {pid: {} for pid in selected_importer.get_playlists()}
            )

            dst = Path("temp_tracks")

            for playlist_id, _ in unique_playlists.items():
                playlist_info = selected_importer.get_playlist(playlist_id)
                for track in playlist_info["tracks"]:
                    unique_tracks[track["id"]] = track
                db_playlist = Playlist(
                    name=playlist_info["title"], owner_id=user_id, public=False
                )
                session.add(db_playlist)
                session.flush()
                cover_path = save_url_file(
                    playlist_info["cover_url"], dst / f"pl-{db_playlist.id}.jpg"
                )
                best_storage = find_best_storage(self.storages, 0)
                best_storage.save_track(cover_path)
                db_playlist.cover_path = f"{best_storage.id}///{cover_path}"
                session.flush()
                playlists_to_add.append(
                    {
                        "importer_id": playlist_id,
                        "db_id": db_playlist.id,
                        "name": playlist_info["title"],
                    }
                )
            for track_id in list(unique_tracks.keys()):
                try:
                    track_info = selected_importer.get_tracks(track_id)
                    title = track_info.get("title", "Unknown")
                    length = track_info.get("length", 0)
                    has_lyrics = track_info.get("has_lyrics", False)
                    album_id = track_info.get("album_id")
                    artists_id = track_info.get("artists", [])

                    if album_id is not None and album_id not in unique_albums:
                        unique_albums[album_id] = {"id": album_id}

                    for artist_id in artists_id:
                        if artist_id not in unique_artists:
                            unique_artists[artist_id] = {"id": artist_id}
                    url, name = selected_importer.get_track_download(track_id, dst)
                    saving_path = Path(
                        (
                            f"{track_info.get('artist_name', 'Unknown')[0]}/{track_info.get('album_title', 'Unknown')}/{name}"
                        ).replace(" ", "-")
                    )
                    best_storage = find_best_storage(
                        self.storages, track_info.get("size", 0)
                    )
                    saved_path = best_storage.save_track(url, saving_path)

                    db_track = Track(
                        title=title,
                        length=length,
                        album_id=album_map.get(album_id) if album_id else None,
                    )
                    track_link = TrackLink(
                        link_type="storage",
                        link_provider=best_storage.id,
                        link=saved_path,
                    )
                    session.add(db_track)
                    session.add(track_link)
                    session.flush()

                    track_map[track_id] = db_track.id
                    tracks_to_add.append(
                        {"id": track_id, "album_id": album_id, "artists_id": artists_id}
                    )
                except:
                    pass
            for artist_id in list(unique_artists.keys()):
                try:
                    artist = selected_importer.get_artists(artist_id)

                    db_artist = Artist(name=artist["name"])
                    session.add(db_artist)
                    session.flush()

                    cover_path = save_url_file(
                        artist["cover_url"], dst / f"ar-{db_artist.id}.jpg"
                    )

                    best_storage = find_best_storage(self.storages, 0)
                    saved_cover_path = best_storage.save_track(cover_path)
                    db_artist.cover_path = f"{best_storage.id}///{saved_cover_path}"

                    session.flush()
                    artist_map[artist_id] = db_artist.id
                except:
                    pass

            for album_id in list(unique_albums.keys()):
                try:
                    album = selected_importer.get_albums(album_id)

                    album_artist_id = None
                    if "artist_id" in album and album["artist_id"] in artist_map:
                        album_artist_id = artist_map[album["artist_id"]]

                    db_album = Album(
                        title=album["title"],
                        year=album.get("year"),
                        artist_id=album_artist_id,
                    )
                    session.add(db_album)
                    session.flush()

                    cover_path = save_url_file(
                        album["cover_url"], dst / f"al-{db_album.id}.jpg"
                    )

                    best_storage = find_best_storage(self.storages, 0)
                    saved_cover_path = best_storage.save_track(cover_path)
                    db_album.cover_path = f"{best_storage.id}///{saved_cover_path}"

                    session.flush()
                    album_map[album_id] = db_album.id
                except:
                    pass

            for playlist_entry in playlists_to_add:
                try:
                    importer_pl_id = playlist_entry["importer_id"]
                    db_pl_id = playlist_entry["db_id"]
                    playlist_info = selected_importer.get_playlist(importer_pl_id)

                    for track in playlist_info["tracks"]:
                        t_id = track["id"]
                        if t_id in track_map:
                            link = PlaylistTrackLink(
                                playlist_id=db_pl_id, track_id=track_map[t_id]
                            )
                            session.add(link)
                            session.flush()
                except:
                    pass
            for track_id in list(track_map.keys()):
                try:
                    lyrics_text = selected_importer.get_lyrics(track_id)
                    if lyrics_text:
                        db_lyrics = Lyrics(
                            value=lyrics_text, track_id=track_map[track_id]
                        )
                        session.add(db_lyrics)
                        session.flush()
                except:
                    pass
            favorited_track_ids = {track["id"] for track in favorited_tracks}
            favorited_album_ids = {album["id"] for album in favorited_albums}
            favorited_artist_ids = {artist["id"] for artist in favorited_artists}

            for track_entry in tracks_to_add:
                try:
                    importer_track_id = track_entry["id"]
                    importer_album_id = track_entry["album_id"]
                    importer_artists_id = track_entry["artists_id"]

                    db_track_id = track_map.get(importer_track_id)
                    if db_track_id is None:
                        continue

                    db_track = session.get(Track, db_track_id)
                    if db_track is None:
                        continue

                    if importer_album_id is not None:
                        db_track.album_id = album_map.get(importer_album_id)

                    for importer_artist_id in importer_artists_id:
                        db_artist_id = artist_map.get(importer_artist_id)
                        if db_artist_id is None:
                            continue

                        session.add(
                            TrackArtistsLink(
                                artist_id=db_artist_id,
                                track_id=db_track.id,
                            )
                        )
                except:
                    pass

            for importer_track_id in favorited_track_ids:
                db_track_id = track_map.get(importer_track_id)
                if db_track_id is not None:
                    session.add(StarredTrack(user_id=user_id, track_id=db_track_id))

            for importer_album_id in favorited_album_ids:
                db_album_id = album_map.get(importer_album_id)
                if db_album_id is not None:
                    session.add(StarredAlbum(user_id=user_id, album_id=db_album_id))

            for importer_artist_id in favorited_artist_ids:
                db_artist_id = artist_map.get(importer_artist_id)
                if db_artist_id is not None:
                    session.add(StarredArtist(user_id=user_id, artist_id=db_artist_id))
            session.commit()

    def checks_status():
        pass
