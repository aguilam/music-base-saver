from pathlib import Path
import tomllib
from structlog import get_logger
from structlog.stdlib import BoundLogger
from search.base import Search as BaseSearch
from downloader.base import Downloader as BaseDownloader
from storage.base import Storage as BaseStorage
from importer.base import Importer as BaseImporter
from scrobbler.base import Scrobbler as BaseScrobbler
from tool.base import Tool as BaseTool
from core.utils import (
    compare_tracks,
    find_best_track,
    full_track_save,
    find_best_storage,
    get_track_metadata_by_path,
    analyze_lrc,
    save_file_from_url,
    image_mime,
    get_video_metadata,
    get_track_metadata_by_bytes,
    get_cover_metadata,
    write_cover_metadata,
)
import shutil
from .db.manager import DBManager
from .db.models import (
    TrackORM,
    ObjectStorageORM,
    AlbumORM,
    ArtistORM,
    StarredAlbum,
    StarredArtist,
    StarredTrack,
    PlaylistORM,
    TrackArtistsLink,
    LyricsORM,
    PlaylistTrackLink,
    PlaylistOwnerORM,
    MusicVideoORM,
    AudioFileORM,
    TrackGenreLink,
    TrackAlbumLink,
    TrackMoodLink,
    AlbumArtistLink,
)
from .schemas.schemas import (
    Artist,
    Album,
    Playlist,
    Track,
    Lyrics,
    MusicVideo,
    Genre,
    Mood,
    LyricsResponse,
    TrackMetadata,
    TrackAlbumMetadata,
    ServiceStatus,
    ServicesStatus,
    SearchResults,
    BinaryBlob,
)
from sqlalchemy import select
from core.loader import import_modules, load_storages, load_modules
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
from typing import Literal, overload
import time
from sqlmodel import Session

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
        self.temp_dir = Path("temp_tracks")
        self.download_queue = {}
        self.sync_queue = {}
        self.search_engines = load_modules(
            config.get("search", {}), import_modules("search", BaseSearch)
        )
        self.storages = load_storages(config, import_modules("storage", BaseStorage))
        self.downloaders = load_modules(
            config.get("downloader", {}), import_modules("downloader", BaseDownloader)
        )
        self.importers = load_modules(
            config.get("importer", {}), import_modules("importer", BaseImporter)
        )
        self.scrobblers = load_modules(
            config.get("scrobbler", {}), import_modules("scrobbler", BaseScrobbler)
        )
        self.scrobblers = load_modules(
            config.get("tool", {}), import_modules("tool", BaseTool)
        )
        self.db_manager = DBManager()
        self.logger: BoundLogger = get_logger(__name__)
        self.executor = ThreadPoolExecutor(max_workers=5)

    def local_search(
        self,
        query: str,
        artistCount: int,
        artistOffset: int,
        albumCount: int,
        albumOffset: int,
        songCount: int,
        songOffset: int,
    ):
        with self.db_manager.get_session() as session:
            return SearchResults(
                artists=self.db_manager.search_artists(
                    session, query, artistCount, artistOffset
                ),
                albums=self.db_manager.search_albums(
                    session, query, albumCount, albumOffset
                ),
                tracks=self.db_manager.search_tracks(
                    session, query, songCount, songOffset
                ),
            )

    def global_search(self, query: str):
        search_results = SearchResults(artists=[], albums=[], tracks=[])
        for engine in self.search_engines:
            search_engine = engine.instance

            res = search_engine.search_tracks(query)
            if res:
                for item in res:
                    item.external_id = f"{search_engine.TAG}-{item.external_id}"
                search_results.tracks.extend(res)

            res = search_engine.search_albums(query)
            if res:
                for item in res:
                    item.external_id = f"{search_engine.TAG}-{item.external_id}"
                search_results.albums.extend(res)

            res = search_engine.search_artists(query)
            if res:
                for item in res:
                    item.external_id = f"{search_engine.TAG}-{item.external_id}"
                search_results.artists.extend(res)

        with self.db_manager.get_session() as session:
            for artist in search_results.artists:
                db_artist = self.db_manager.get_artist_by_name(session, artist.name)
                artist.id = db_artist.id if db_artist else None
            for album in search_results.albums:
                db_album = self.db_manager.get_album_by_name(session, album.title)
                album.id = db_album.id if db_album else None
            for track in search_results.tracks:
                db_track = self.db_manager.get_track_by_name(session, track.title)
                track.id = db_track.id if db_track else None
        return search_results

    @overload
    def get_global_object(
        self, object_type: Literal["track"], object_id: str
    ) -> Track: ...
    @overload
    def get_global_object(
        self, object_type: Literal["album"], object_id: str
    ) -> Album: ...
    @overload
    def get_global_object(
        self, object_type: Literal["artist"], object_id: str
    ) -> Artist: ...

    def get_global_object(
        self, object_type: Literal["track", "album", "artist"], object_id: str
    ):
        parts = object_id.split("-", 1)
        search_tag = parts[0]
        search_id = parts[1]
        for engine in self.search_engines:
            if engine.tag == search_tag:
                search_engine = engine.instance
                if object_type == "track":
                    return search_engine.get_track(search_id)
                elif object_type == "album":
                    album = search_engine.get_album(search_id)
                    for track in album.tracks:
                        track.external_id = f"{engine.tag}-{track.external_id}"
                    return album
                elif object_type == "artist":
                    artist = search_engine.get_artist(search_id)
                    for album in artist.albums:
                        album.external_id = f"{engine.tag}-{album.external_id}"
                    return artist

    def get_download_task(self, task_id: str):
        return self.download_queue.get(task_id)

    def post_download(self, query: str | None = None, object_id: str | None = None):
        task_id = str(uuid4())[:8]
        self.download_queue[task_id] = {"status": "Processing", "progress": 0}
        self.executor.submit(self.download, task_id, query, object_id)
        return task_id

    def _update_progress(self, task_id: str, progress: int):
        self.download_queue[task_id]["progress"] = progress

    def add_new_track(
        self,
        session: Session,
        track_metadata: TrackMetadata,
        track_info: dict,
        storage_id: str,
        cover_id: int | None = None,
    ):
        db_album = None
        track_artists = [
            self.db_manager.find_or_create_artist(session, artist)
            for artist in track_metadata.artists
        ]
        new_track = TrackORM(
            title=track_metadata.title,
            length=track_metadata.length,
            bpm=track_metadata.bpm,
            year=track_metadata.year,
        )
        session.add(new_track)
        session.flush()
        for album in track_metadata.albums:
            db_album = self.db_manager.find_or_create_album(
                session, album.title, album.album_artists
            )
            if db_album.cover_path is None and cover_id:
                db_album.cover_path = cover_id
            session.add(db_album)
            session.flush()
            db_album_artists = [
                self.db_manager.find_or_create_artist(session, artist)
                for artist in album.album_artists
            ]
            album_artists = [
                AlbumArtistLink(artist_id=artist.id, album_id=db_album.id)
                for artist in db_album_artists
            ]
            track_album = TrackAlbumLink(
                track_id=new_track.id,
                album_id=db_album.id,
                album_position=album.album_position,
                disc_number=album.disc_number,
            )
            session.add(track_album)
            session.add_all(album_artists)
            session.flush()
        for genre in track_metadata.genres:
            track_genre = self.db_manager.find_or_create_genre(session, genre)
            track_genre_link = TrackGenreLink(
                track_id=new_track.id, genre_id=track_genre.id
            )
            session.add(track_genre_link)
            session.flush()
        for mood in track_metadata.moods:
            track_mood = self.db_manager.find_or_create_mood(session, mood)
            track_mood_link = TrackMoodLink(
                track_id=new_track.id, mood_id=track_mood.id
            )
            session.add(track_mood_link)
            session.flush()
        audio_file = AudioFileORM(track_id=new_track.id, bitrate=track_metadata.bitrate)
        new_track.files.append(audio_file)
        session.add(audio_file)
        session.flush()
        new_link = ObjectStorageORM(
            link_type="storage",
            audio_id=audio_file.id,
            file_name=track_info["file_name"],
            link_provider=storage_id,
            link=track_info["link"],
        )
        session.add(new_link)
        for artist in track_artists:
            track_artist = TrackArtistsLink(artist_id=artist.id, track_id=new_track.id)
            session.add(track_artist)
        session.flush()
        return new_track.id

    def download(
        self,
        task_id: str,
        query: str | None = None,
        object_id: str | None = None,
    ):
        if query is None and object_id is None:
            return None
        downloaders = self.downloaders
        original_track: Track | None = None

        tracks_dict = []
        searched_tracks = []
        if query:
            search_results = self.global_search(query).tracks
            if len(search_results) < 1:
                return None
            original_track = find_best_track(search_results)
        elif object_id:
            track = self.get_global_object("track", object_id)
            original_track = track
        if original_track is None:
            return None
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
            saving_path = Path((f"{artist_name}/{album_title}/{dst.name}"))
            best_storage = find_best_storage(self.storages, best_track["size"])
            paths = full_track_save(best_storage, dst, saving_path)
            cover_storage_path = paths["cover_path"]
            saved_path = paths["track_path"]
            with self.db_manager.get_session() as session:
                cover = ObjectStorageORM(
                    link_type="storage",
                    file_name=Path(cover_storage_path).name,
                    link_provider=best_storage.id,
                    link=cover_storage_path,
                )
                session.add(cover)
                session.flush(cover)
                self.add_new_track(
                    session,
                    track,
                    {"link": saved_path, "file_name": dst.name},
                    best_storage.id,
                    cover.id,
                )
                session.commit()
            self.download_queue[task_id]["result"] = {
                "title": title,
                "artist": track.artists,
                "length": track.length,
                "storage": best_storage.name,
                "download_source": downloader.TAG,
                "saved_path": saved_path,
            }
            self.download_queue[task_id]["status"] = "Finished"

    def get_file(self, path: str, storage_id: str):
        for storage in self.storages:
            current_storage = storage.instance
            if current_storage.id == storage_id:
                cover_path = current_storage.get_file(path)
                return Path(cover_path).read_bytes()

    def get_all_tracks(self):
        with self.db_manager.get_session() as session:
            tracks = self.db_manager.get_all_tracks(session)
            return tracks

    def get_all_artists(self):
        with self.db_manager.get_session() as session:
            artists = self.db_manager.get_all_artists(session)
            return artists

    def get_all_albums(self):
        with self.db_manager.get_session() as session:
            albums = self.db_manager.get_all_albums(session)
            return albums

    def get_track_by_id(self, id: int):
        with self.db_manager.get_session() as session:
            track = self.db_manager.get_track_by_id(session, id)
            return track

    def scrobble(self, id: int, user_id: str, listen_time: int | None = None):
        with self.db_manager.get_session() as session:
            track = self.db_manager.get_track_by_id(session, id)
            if listen_time is None:
                listen_time = int(time.time())
            for scrobbler in self.scrobblers:
                provider_key = self.db_manager.get_provider_key(
                    session, scrobbler.tag, user_id
                )
                if provider_key is None:
                    continue
                scrobbler_class = scrobbler.instance
                scrobbler_class.submit_listen(track, provider_key, listen_time)

    def post_now_playing(self, id: int, user_id: str):
        with self.db_manager.get_session() as session:
            track = self.db_manager.get_track_by_id(session, id)
            for scrobbler in self.scrobblers:
                provider_key = self.db_manager.get_provider_key(
                    session, scrobbler.tag, user_id
                )
                if provider_key is None:
                    continue
                scrobbler_class = scrobbler.instance
                scrobbler_class.post_playing_now(track, provider_key)

    def get_album_by_id(self, id: int):
        with self.db_manager.get_session() as session:
            album = self.db_manager.get_album_by_id(session, id)
            return album

    def get_artist_by_id(self, id: int):
        with self.db_manager.get_session() as session:
            artist = self.db_manager.get_artist_by_id(session, id)
            return artist

    def get_artist_top_songs(self, name: str, count: int):
        with self.db_manager.get_session() as session:
            artist_tracks = self.db_manager.get_tracks_by_artist_name(session, name)
            return artist_tracks[:50]

    def get_cover_art(self, id: int):
        with self.db_manager.get_session() as session:
            storage = self.db_manager.get_storage_object_by_id(session, id)
            if storage is None:
                return None
            cover_art = self.get_file(storage.link, storage.link_provider)
            cover_mime = image_mime(cover_art)
            return BinaryBlob(cover_art, cover_mime)

    def get_genres(self):
        with self.db_manager.get_session() as session:
            genres = self.db_manager.get_genres(session)
            counted_genres = []
            for genre in genres:
                counted_genres.append(
                    {
                        "name": genre.name,
                        "track_count": len(genre.tracks),
                        "album_count": len(genre.albums),
                    }
                )
            return counted_genres

    def get_moods(self):
        with self.db_manager.get_session() as session:
            moods = self.db_manager.get_moods(session)
            counted_moods = []
            for mood in moods:
                albums_ids = {}
                for track in mood.tracks:
                    albums_ids.update(album.id for album in track.albums)
                counted_moods.append(
                    {
                        "name": mood.name,
                        "track_count": len(mood.tracks),
                        "album_count": len(albums_ids),
                    }
                )
            return counted_moods

    def get_playlist_by_id(self, id: int):
        with self.db_manager.get_session() as session:
            playlist = self.db_manager.get_playlist_by_id(session, id)
            if playlist is None:
                return None
            if playlist:
                session.expunge_all()
            return playlist

    def delete_user_by_username(self, username: str, user_id: int):
        with self.db_manager.get_session() as session:
            user = self.db_manager.get_user_by_id(session, user_id)
            if user.is_admin or user.username == username:
                return self.db_manager.delete_user_by_username(session, username)
            return None

    def delete_user_by_id(self, id: int, user_id: int):
        with self.db_manager.get_session() as session:
            user = self.db_manager.get_user_by_id(session, user_id)
            if user.is_admin or user.id == id:
                return self.db_manager.delete_user_by_id(session, id)
            return None

    def delete_track(self, track_id: int):
        with self.db_manager.get_session() as session:
            track = self.db_manager.delete_track(session, track_id)
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

    def get_user_playlists(self, user_id: int):
        with self.db_manager.get_session() as session:
            return self.db_manager.get_user_playlists(session, user_id)

    def create_playlist(
        self,
        user_id: int,
        name: str | None,
        tracks_id: list[int],
        is_public: bool = False,
        cover_path: int | None = None,
    ):
        with self.db_manager.get_session() as session:
            new_playlist = self.db_manager.create_playlist(
                session, user_id, name, cover_path, is_public, tracks_id
            )
            session.commit()
            return new_playlist

    def update_user(
        self,
        user_id: int,
        username: str | None = None,
        password: str | None = None,
        is_admin: bool | None = None,
    ):
        with self.db_manager.get_session() as session:
            user = self.db_manager.update_user(
                session, user_id, username, password, is_admin
            )
            session.commit()
            return user

    def create_user(self, username: str, email: str, password: str):
        with self.db_manager.get_session() as session:
            new_user = self.db_manager.create_user(username, email, password)
            session.commit()
            return new_user

    def delete_playlist(self, playlist_id: int):
        with self.db_manager.get_session() as session:
            self.db_manager.delete_playlist(playlist_id)
            session.commit()

    def get_all_albums(self):
        with self.db_manager.get_session() as session:
            return self.db_manager.get_all_albums(session)

    def get_all_user_starred(self, user_id: int):
        with self.db_manager.get_session() as session:
            return self.db_manager.get_all_user_starred(session, user_id)

    def get_track_by_title(self, title: str):
        with self.db_manager.get_session() as session:
            return self.db_manager.get_track_by_name(session, title)

    def get_lyrics(self, track_id: int):
        with self.db_manager.get_session() as session:
            track = self.db_manager.get_track_by_id(session, track_id)
            if track is None:
                return None
            artists_name = ", ".join([artist.name for artist in track.artists])
            lyrics_list: list[LyricsResponse] = []
            for lyrics in track.lyrics:
                lyrics_list.append(
                    LyricsResponse(
                        lyrics.id,
                        artists_name,
                        track.title,
                        lyrics.is_synced,
                        lyrics.synced_text,
                        lyrics.plain_text,
                        lyrics.language,
                        lyrics.offset,
                    )
                )
            return lyrics_list

    def get_user(self, username: str | None = None, apiKey: str | None = None):
        with self.db_manager.get_session() as session:
            if username is not None:
                return self.db_manager.get_user_by_name(session, username)
            elif apiKey is not None:
                return self.db_manager.get_user_by_apikey(session, apiKey)
            else:
                return None

    def stream_track(self, id: int, start_bytes: int, end_bytes: int):
        with self.db_manager.get_session() as session:
            object_id = None
            if "cl-" in str(id):
                video_id = str(id).split("-")[1]
                video = self.db_manager.get_video_by_id(session, int(video_id))
                object_id = video.local_link
            else:
                track = self.db_manager.get_track_by_id(session, int(id))
                object_id = track.path
            if object_id is None:
                return None
            storage = self.db_manager.get_storage_object_by_id(session, object_id)
            media_storage = storage.link_provider
            media_link = storage.link
            for storage in self.storages:
                current_storage = storage.instance
                if current_storage.id == media_storage:
                    track = current_storage.get_range_bytes(
                        media_link, start_bytes, end_bytes
                    )
                    return track

    def get_sync_task(self, task_id: str):
        return self.sync_queue.get(task_id)

    def post_sync(self, storage_id: str | None = None, sync_id: str | None = None):
        task_id = str(uuid4())[:8] if sync_id is None else sync_id
        self.sync_queue[task_id] = {"status": "Processing", "deleted": 0, "added": 0}
        self.executor.submit(self.sync, task_id)
        return task_id

    def _update_sync_progress(self, task_id: str, deleted: int = 0, added: int = 0):
        self.sync_queue[task_id]["deleted"] += deleted
        self.sync_queue[task_id]["added"] += added

    def save_object(
        self, session: Session, file_path: str, saving_path: str, file_size: int = 0
    ):
        best_storage = find_best_storage(self.storages, file_size)
        saved_object_path = best_storage.instance.save_file(file_path, saving_path)
        object_storage = ObjectStorageORM(
            link_type="storage",
            link_provider=best_storage.id,
            link=saved_object_path,
        )
        session.add(object_storage)
        session.flush()
        return object_storage.id

    def sync(self, task_id: str):
        try:
            with self.db_manager.get_session() as session:
                db_tracks = self.db_manager.get_all_tracks_storage_links(session)
                storaged_tracks: set[tuple[str, str]] = set()
                for storage in self.storages:
                    current_storage = storage.instance
                    tracks_path = current_storage.get_all_tracks_paths()
                    named_paths = [
                        (f"{storage.id}///{link}", file_name)
                        for link, file_name in tracks_path
                    ]
                    storaged_tracks.update(named_paths)
                deleted_objects_links = db_tracks - storaged_tracks
                added_object_links = storaged_tracks - db_tracks
                objects_for_deleting = [
                    (track.split("///")[0], track.split("///")[1])
                    for track, _ in deleted_objects_links
                ]
                deleted_count = self.db_manager.bulk_delete_by_links(
                    session, objects_for_deleting
                )
                self._update_sync_progress(task_id, deleted=deleted_count)
                tracks_to_adding = {}
                cover_to_adding = {}
                lyrics_to_adding = {}
                videos_to_adding = {}
                track_added_count = 0
                cover_added_count = 0
                for link, file_name in added_object_links:
                    k, v = link.split("///")
                    if any(ext in v for ext in ["jpeg", "jpg", "png"]):
                        if k in cover_to_adding:
                            cover_to_adding[k].append(
                                {"link": v, "file_name": file_name}
                            )
                        else:
                            cover_to_adding[k] = [{"link": v, "file_name": file_name}]
                    elif any(ext in v for ext in ["lrc", "txt"]):
                        if k in lyrics_to_adding:
                            lyrics_to_adding[k].append(
                                {"link": v, "file_name": file_name}
                            )
                        else:
                            lyrics_to_adding[k] = [{"link": v, "file_name": file_name}]
                    elif "mp4" in v:
                        if k in videos_to_adding:
                            videos_to_adding[k].append(
                                {"link": v, "file_name": file_name}
                            )
                        else:
                            videos_to_adding[k] = [{"link": v, "file_name": file_name}]
                    elif any(ext in v for ext in ["m4a", "flac", "mp3", "opus"]):
                        if k in tracks_to_adding:
                            tracks_to_adding[k].append(
                                {"link": v, "file_name": file_name}
                            )
                        else:
                            tracks_to_adding[k] = [{"link": v, "file_name": file_name}]
                for storage in self.storages:
                    current_storage = storage.instance
                    if storage.id in tracks_to_adding:
                        for track in tracks_to_adding[storage.id]:
                            track_bytes = current_storage.get_range_bytes(
                                track["link"], 0, 1024 * 1024 * 5
                            )["bytes"]
                            track_metadata = get_track_metadata_by_bytes(track_bytes)
                            self.add_new_track(
                                session, track_metadata, track, storage.id
                            )
                            track_added_count += 1
                            self._update_sync_progress(task_id, added=1)
                    if storage.id in cover_to_adding:
                        for cover in cover_to_adding[storage.id]:
                            content_id = None
                            content_type = None
                            entity = None
                            range_bytes: bytes = current_storage.get_range_bytes(
                                cover["link"], 0, 99999999
                            )["bytes"]
                            id_from_cover = get_cover_metadata(
                                range_bytes, "png" in cover["file_name"]
                            )
                            if id_from_cover is None:
                                if "-" not in cover["file_name"]:
                                    continue
                                subject, subject_id = cover["file_name"].split("-")
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
                                file_path = current_storage.get_file(cover["link"])
                                write_cover_metadata(
                                    file_path, f"{content_type}-{content_id}"
                                )
                            else:
                                subject, subject_id = id_from_cover.split("-")
                                content_type = subject
                                content_id = int(subject_id)
                            if content_id is None or content_type is None:
                                continue
                            if content_type == "al":
                                entity = self.db_manager.get_album_orm_by_id(
                                    session, content_id
                                )
                            elif content_type == "ar":
                                entity = self.db_manager.get_artist_orm_by_id(
                                    session, content_id
                                )
                            elif content_type == "pl":
                                entity = self.db_manager.get_playlist_orm_by_id(
                                    session, content_id
                                )
                            if entity is None:
                                continue
                            cover_storage = ObjectStorageORM(
                                link_type="storage",
                                link_provider=storage.id,
                                link=cover["link"],
                                file_name=cover["file_name"],
                            )
                            session.add(cover_storage)
                            session.flush()
                            entity.cover_path = cover_storage.id
                            session.flush()
                            cover_added_count += 1
                            self._update_sync_progress(task_id, added=1)
                    if storage.id in lyrics_to_adding:
                        for lyrics in lyrics_to_adding[storage.id]:
                            range_bytes: bytes = current_storage.get_range_bytes(
                                lyrics["link"], 0, 9999999
                            )["bytes"]
                            text = range_bytes.decode()
                            if ".lrc" in lyrics["link"]:
                                file_content = analyze_lrc(text.splitlines())
                                track = self.db_manager.get_track_by_name(
                                    session, file_content["title"]
                                )
                                if track is None:
                                    continue
                                new_lyrics = LyricsORM(
                                    is_synced=True,
                                    language="und",
                                    synced_text=file_content["text"],
                                    offset=file_content["offset"],
                                    track_id=track.id,
                                )
                                session.add(new_lyrics)
                                session.flush()
                                lyrics_path = ObjectStorageORM(
                                    link_type="storage",
                                    link_provider=storage.id,
                                    link=lyrics["link"],
                                    file_name=lyrics["file_name"],
                                )
                                new_lyrics.path.append(lyrics_path)
                                session.add(lyrics_path)
                                session.flush()
                            elif ".txt" in lyrics["link"]:
                                track = self.db_manager.get_track_by_name(
                                    session, lyrics["file_name"].split(".")[0]
                                )
                                if track is None:
                                    continue
                                new_lyrics = LyricsORM(
                                    is_synced=False,
                                    language="und",
                                    plain_text=text,
                                    track_id=track.id,
                                )
                                session.add(new_lyrics)
                                session.flush()
                                lyrics_path = ObjectStorageORM(
                                    link_type="storage",
                                    link_provider=storage.id,
                                    link=lyrics["link"],
                                    lyrics_id=new_lyrics.id,
                                    file_name=lyrics["file_name"],
                                )
                                new_lyrics.path.append(lyrics_path)
                                session.add(lyrics_path)
                                session.flush()
                    if storage.id in videos_to_adding:
                        for video in videos_to_adding[storage.id]:
                            video_bytes = current_storage.get_range_bytes(
                                video["link"], 0, 1024 * 1024 * 5
                            )["bytes"]
                            video_metadata = get_video_metadata(video_bytes)
                            video_title = video_metadata["title"]
                            if video_title is None:
                                video_title = video["file_name"].split(".")[0]
                            track = self.db_manager.get_track_by_name(
                                session, video_title
                            )
                            if track is None:
                                id_parts = video["file_name"].split(".")[0].rsplit("-")
                                if len(id_parts) == 2 and id_parts[0] == "tr":
                                    track = self.db_manager.get_track_by_id(id_parts[1])

                            if track is None:
                                continue
                            music_video = MusicVideoORM(
                                is_external_link=False,
                                track_id=track.id,
                            )
                            session.add(music_video)
                            session.flush()
                            video_storage = ObjectStorageORM(
                                link_type="storage",
                                link_provider=storage.id,
                                link=video["link"],
                                file_name=video["file_name"],
                            )
                            music_video.local_link.append(video_storage)
                            session.add(music_video)
                            session.flush()
                session.commit()
                self.sync_queue[task_id]["status"] = "Finished"
                self.logger.info("Syncing succesful completed")
        except:
            self.logger.warning("Problem in library syncing")

    def import_tracks(self, importer_tag: str, user_id: int | None = None):
        importers = self.importers
        selected_importer = None
        for importer in importers:
            if importer.tag == importer_tag:
                selected_importer = importer.instance
                break
        with self.db_manager.get_session() as session:
            (
                favorited_tracks,
                favorited_albums,
                favorited_artists,
                favorited_playlists,
            ) = selected_importer.get_favorited()
            if user_id:
                owner = self.db_manager.get_user_by_id(session, user_id)
            user_id = 1 if user_id is None or owner is None else user_id

            unique_tracks_ids = {*favorited_tracks}
            unique_albums_ids = {*favorited_albums}
            unique_artists_ids = {*favorited_artists}
            unique_playlists_ids = {*favorited_playlists}
            playlists_to_add = []
            tracks_to_add = []
            artist_map: dict[int | str, int] = {}
            album_map: dict[int | str, int] = {}
            track_map: dict[int | str, int] = {}
            tracks_with_lyrics = []
            tracks_with_music_videos = []
            album_artist_link = {}
            track_artist_link = {}
            track_album_link = {}
            unique_playlists_ids.update(selected_importer.get_user_playlists())

            dst = self.temp_dir

            for playlist_id in unique_playlists_ids:
                try:
                    playlist_info = selected_importer.get_playlist(playlist_id)
                    unique_tracks_ids.update(playlist_info.track_ids)
                    db_playlist = PlaylistORM(name=playlist_info.title, is_public=False)
                    session.add(db_playlist)
                    session.flush()
                    playlist_owner = PlaylistOwnerORM(
                        owner_id=user_id, playlist_id=db_playlist.id
                    )
                    session.add(playlist_owner)
                    session.flush()
                    playlists_to_add.append(
                        {
                            "importer_id": playlist_id,
                            "db_id": db_playlist.id,
                        }
                    )
                    cover_name = f"pl-{playlist_info.title}.jpg"
                    cover_path = dst / cover_name
                    save_file_from_url(playlist_info.cover_uri, cover_path)
                    cover_id = self.save_object(session, cover_path, cover_name)
                    db_playlist.cover_path = cover_id
                    session.flush()
                except:
                    self.logger.warning(
                        "Problem in importing playlist",
                        importer=importer_tag,
                        user_id=user_id,
                        playlist_id=playlist_id,
                    )

            for track_id in unique_tracks_ids:
                try:
                    track_info = selected_importer.get_track(track_id)
                    if track_info.has_lyrics:
                        tracks_with_lyrics.append(track_id)
                    if track_info.has_video:
                        tracks_with_music_videos.append(track_id)
                    unique_albums_ids.update(track_info.albums)
                    unique_artists_ids.update(track_info.artists)
                    url, name = selected_importer.get_track_download_link(track_id)
                    track_dst = dst / name
                    save_file_from_url(url, track_dst)
                    saving_path = Path(
                        (
                            f"{track_info.main_artist_name}/{track_info.main_album_title}/{name}"
                        )
                    )
                    best_storage = find_best_storage(
                        self.storages, track_info.get("size", 0)
                    )
                    saved_path = best_storage.instance.save_file(track_dst, saving_path)
                    db_track_id = self.add_new_track(
                        session,
                        TrackMetadata(title=track_info.title, length=track_info.length),
                        {"link": saved_path, "filename": name},
                        best_storage.id,
                    )
                    for album_id in track_info.albums:
                        if album_id in track_album_link:
                            track_album_link[album_id] = [db_track_id]
                        else:
                            track_album_link[album_id].append(db_track_id)
                    for artist_id in track_info.artists:
                        if artist_id in track_artist_link:
                            track_artist_link[artist_id] = [db_track_id]
                        else:
                            track_artist_link[artist_id].append(db_track_id)
                except Exception as e:
                    self.logger.warning(
                        "Problem in importing track",
                        importer=importer_tag,
                        user_id=user_id,
                        track_id=track_id,
                        error=str(e),
                    )

            for album_id in unique_albums_ids:
                try:
                    album = selected_importer.get_album(album_id)
                    unique_artists_ids.update(album.artist_ids)

                    db_album = AlbumORM(
                        title=album.title,
                        year=album.year,
                        description=album.description,
                    )
                    session.add(db_album)
                    session.flush()

                    cover_path = save_file_from_url(
                        album.cover_uri, dst / f"al-{db_album.title}.jpg"
                    )

                    cover_id = self.save_object(session, cover_path)
                    db_album.cover_path = cover_id
                    session.flush()
                    album_map[album_id] = db_album.id
                    track_links = []
                    for track_id in track_album_link:
                        track_links.append(
                            TrackAlbumLink(track_id=track_id, album_id=db_album.id)
                        )
                    session.add_all(track_links)
                    session.flush()
                    for artist_id in track_info.artists:
                        if artist_id in album_artist_link:
                            album_artist_link[artist_id] = [album_id]
                        else:
                            album_artist_link[artist_id].append(album_id)
                except Exception as e:
                    self.logger.warning(
                        "Problem in importing album",
                        importer=importer_tag,
                        user_id=user_id,
                        album_id=album_id,
                        error=str(e),
                    )

            for artist_id in unique_artists_ids:
                try:
                    artist = selected_importer.get_artist(artist_id)

                    db_artist = self.db_manager.find_or_create_artist(
                        session, artist.name
                    )

                    db_artist.description = artist.description
                    cover_path = f"ar-{db_artist.name}.jpg"
                    save_file_from_url(artist.cover_uri, dst / cover_path)
                    cover_id = self.save_object(
                        session, cover_path, f"{db_artist.name}/cover.jpg"
                    )
                    db_artist.cover_path = cover_id
                    session.flush()
                    album_artist_links = []
                    track_artist_links = []
                    for album_id in album_artist_link:
                        album_artist_links.append(
                            AlbumArtistLink(album_id=album_id, artist_id=db_artist.id)
                        )
                    for track_id in track_artist_link:
                        track_artist_links.append(
                            TrackArtistsLink(track_id=track_id, artist_id=db_artist.id)
                        )
                    session.add_all(album_artist_links)
                    session.add_all(track_artist_links)
                    session.flush()
                    artist_map[artist_id] = db_artist.id
                except Exception as e:
                    self.logger.warning(
                        "Problem in importing artist",
                        importer=importer_tag,
                        user_id=user_id,
                        artist_id=artist_id,
                        error=str(e),
                    )

            for playlist_entry in playlists_to_add:
                try:
                    playlist_info = selected_importer.get_playlist(
                        playlist_entry["importer_id"]
                    )

                    for track in playlist_info.track_ids:
                        if track in track_map:
                            link = PlaylistTrackLink(
                                playlist_id=playlist_entry["db_id"],
                                track_id=track_map[track],
                            )
                            session.add(link)
                            session.flush()
                except Exception as e:
                    self.logger.warning(
                        "Problem in importing playlist",
                        importer=importer_tag,
                        user_id=user_id,
                        playlist_id=playlist_entry["importer_id"],
                        error=str(e),
                    )

            for track_id in tracks_with_lyrics:
                try:
                    url, name = selected_importer.get_lyrics_download_link(track_id)
                    saved_path = dst / name
                    save_file_from_url(url, saved_path)
                    text = saved_path.read_text()
                    if ".lrc" in name:
                        file_content = analyze_lrc(text.splitlines())
                        track = self.db_manager.get_track_by_name(
                            session, file_content["title"]
                        )
                        if track is None:
                            continue
                        new_lyrics = LyricsORM(
                            is_synced=True,
                            language="und",
                            synced_text=file_content["text"],
                            offset=file_content["offset"],
                            track_id=track.id,
                        )
                        session.add(new_lyrics)
                        session.flush()
                    elif ".txt" in name:
                        track = self.db_manager.get_track_by_name(
                            session, name.split(".")[0]
                        )
                        if track is None:
                            continue
                        new_lyrics = LyricsORM(
                            is_synced=False,
                            language="und",
                            plain_text=text,
                            track_id=track.id,
                        )
                        session.add(new_lyrics)
                        session.flush()
                    best_storage = find_best_storage(
                        self.storages, track_info.get("size", 0)
                    )
                    saved_link = best_storage.instance.save_file(track_dst, saving_path)
                    lyrics_path = ObjectStorageORM(
                        link_type="storage",
                        link_provider=best_storage.id,
                        link=saved_link,
                        lyrics_id=new_lyrics.id,
                        file_name=saved_path.name,
                    )
                    new_lyrics.path.append(lyrics_path)
                    session.add(lyrics_path)
                    session.flush()
                except Exception as e:
                    self.logger.warning(
                        "Problem in importing track lyrics",
                        importer=importer_tag,
                        user_id=user_id,
                        track_id=track_id,
                        error=str(e),
                    )

            for track_id in tracks_with_music_videos:
                try:
                    url, name = selected_importer.get_music_video_download_link(
                        track_id
                    )

                    save_file_from_url(url, dst / name)
                    best_storage = find_best_storage(
                        self.storages, track_info.get("size", 0)
                    )
                    db_track = track_map[track_id]
                    music_video = MusicVideoORM(track_id=db_track)
                    session.add(music_video)
                    session.flush()
                    saved_link = best_storage.instance.save_file(track_dst, saving_path)
                    video_path = ObjectStorageORM(
                        link_type="storage",
                        link_provider=best_storage.id,
                        link=saved_link,
                        music_video_id=music_video.id,
                        file_name=name,
                    )
                    music_video.local_link.append(video_path)
                    session.add(video_path)
                    session.flush()
                except Exception as e:
                    self.logger.warning(
                        "Problem in adding imported music video",
                        importer=importer_tag,
                        user_id=user_id,
                        track_id=track_id,
                        error=str(e),
                    )

            for importer_track_id in favorited_tracks:
                db_track_id = track_map.get(importer_track_id)
                if db_track_id is not None:
                    session.add(StarredTrack(user_id=user_id, track_id=db_track_id))

            for importer_album_id in favorited_albums:
                db_album_id = album_map.get(importer_album_id)
                if db_album_id is not None:
                    session.add(StarredAlbum(user_id=user_id, album_id=db_album_id))

            for importer_artist_id in favorited_artists:
                db_artist_id = artist_map.get(importer_artist_id)
                if db_artist_id is not None:
                    session.add(StarredArtist(user_id=user_id, artist_id=db_artist_id))

            session.commit()
            self.logger.info(
                "Succesful imported library", importer=importer_tag, user_id=user_id
            )

    def check_status(self):
        return ServicesStatus(
            downloaders=[
                ServiceStatus(
                    tag=downloader.tag, health=downloader.instance.health_check()
                )
                for downloader in self.downloaders
            ],
            importers=[
                ServiceStatus(tag=importer.tag, health=importer.instance.health_check())
                for importer in self.importers
            ],
            scrobblers=[
                ServiceStatus(
                    tag=scrobbler.tag, health=scrobbler.instance.health_check()
                )
                for scrobbler in self.scrobblers
            ],
            search=[
                ServiceStatus(tag=search.tag, health=search.instance.health_check())
                for search in self.search_engines
            ],
            storages=[
                ServiceStatus(tag=storage.tag, health=storage.instance.health_check())
                for storage in self.storages
            ],
        )
