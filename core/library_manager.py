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
from collections import defaultdict
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
    write_track_metadata,
    write_video_metadata,
    _get_runtime_errors,
    sanitize_filename,
    read_lyrics_text,
    get_id_from_string,
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
    AlbumGenreLink,
    ArtistGenreLink,
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
    FilePathInfo,
    Task,
    SyncTaskResult,
    DownloadTaskResult,
    ImportTaskResult,
    ImporterPlaylistTrack,
    LibraryStats,
    StartStatuses,
)
from sqlalchemy import select
from core.loader import import_modules, load_storages, load_modules
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
from typing import Literal, overload, cast
import time
import os
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
        self.task_queue: dict[str, Task] = {}
        self.start_errors: StartStatuses = StartStatuses()
        self.search_engines, self.start_errors.search = load_modules(
            config.get("search", {}), import_modules("search", BaseSearch)
        )
        self.storages, self.start_errors.storages = load_storages(
            config, import_modules("storage", BaseStorage)
        )
        self.downloaders, self.start_errors.downloaders = load_modules(
            config.get("downloader", {}), import_modules("downloader", BaseDownloader)
        )
        self.importers, self.start_errors.importers = load_modules(
            config.get("importer", {}), import_modules("importer", BaseImporter)
        )
        self.scrobblers, self.start_errors.scrobblers = load_modules(
            config.get("scrobbler", {}), import_modules("scrobbler", BaseScrobbler)
        )
        self.tools = load_modules(
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

    def add_new_track(
        self,
        session: Session,
        track_metadata: TrackMetadata,
        track_info: FilePathInfo,
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
            normalized_title=track_metadata.title.strip().lower(),
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
            for artist in db_album_artists:
                exists = session.exec(
                    select(AlbumArtistLink).where(
                        AlbumArtistLink.artist_id == artist.id,
                        AlbumArtistLink.album_id == db_album.id,
                    )
                ).first()

                if not exists:
                    session.add(
                        AlbumArtistLink(artist_id=artist.id, album_id=db_album.id)
                    )
            track_album = TrackAlbumLink(
                track_id=new_track.id,
                album_id=db_album.id,
                album_position=album.album_position,
                disc_number=album.disc_number,
            )
            session.add(track_album)
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
        audio_file = AudioFileORM(
            track_id=new_track.id, bitrate=track_metadata.bitrate, is_primary=True
        )
        new_track.files.append(audio_file)
        session.add(audio_file)
        session.flush()
        new_link = ObjectStorageORM(
            link_type="storage",
            audio_id=audio_file.id,
            file_name=track_info.filename,
            link_provider=storage_id,
            link=track_info.link,
        )
        session.add(new_link)
        for artist in track_artists:
            track_artist = TrackArtistsLink(artist_id=artist.id, track_id=new_track.id)
            session.add(track_artist)
        session.flush()
        return new_track.id

    def get_similiar_artists_random_tracks(self, artist_id: int, count: int):
        with self.db_manager.get_session() as session:
            artist = self.db_manager.get_artist_by_id(session, artist_id)
            if artist is None:
                return None
            artists = self.scrobblers[0].instance.get_similiar_artists(artist)
            tracks = self.db_manager.get_artists_random_tracks(session, artists, count)
            return tracks

    def get_user_tracks_recommendations(self, user_id: int, count: int):
        with self.db_manager.get_session() as session:
            scrobbler = self.scrobblers[0]
            provider_key = self.db_manager.get_provider_key(
                session, scrobbler.tag, user_id
            )
            if provider_key is None:
                return None
            tracks = scrobbler.instance.get_tracks_recommendations(
                provider_key.key, count
            )
            db_tracks: list[Track] = []
            for track in tracks:
                album_name = next((album.title for album in track.albums), None)
                artists_names = [artist.name for artist in track.artists]
                db_track = self.db_manager.find_track(
                    session, track.title, album_name, artists_names
                )
                if db_track is not None:
                    db_tracks.append(db_track)
            return db_tracks

    def download(
        self,
        task_id: str | None = None,
        query: str | None = None,
        object_id: str | None = None,
    ):
        task_id = self.post_task(
            func=self.download_track, task_id=task_id, query=query, object_id=object_id
        )
        return task_id

    def download_track(
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
                    FilePathInfo(link=saved_path, filename=dst.name),
                    best_storage.id,
                    cover.id,
                )
                session.commit()
            self.task_queue[task_id].result = DownloadTaskResult(
                title=title,
                artist=track.artists,
                length=track.length,
                storage=best_storage.name,
                download_source=downloader.TAG,
                saved_path=saved_path,
            )
            self._update_task(task_id, status="finished")

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
                scrobbler_class.submit_listen(track, provider_key.key, listen_time)

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
                scrobbler_class.post_playing_now(track, provider_key.key)

    def delete_provider_key(self, key_id: int):
        with self.db_manager.get_session() as session:
            self.db_manager.delete_provider_key(session, key_id)
            session.commit()

    def check_api_key_availability(self, api_key: str):
        with self.db_manager.get_session() as session:
            key = self.db_manager.check_api_key_availability(session, api_key)
            return key

    def get_user_provider_keys(self, user_id: int):
        with self.db_manager.get_session() as session:
            api_keys = self.db_manager.get_user_provider_keys(session, user_id)
            return api_keys

    def get_user_api_keys(self, user_id: int):
        with self.db_manager.get_session() as session:
            api_keys = self.db_manager.get_user_api_keys(session, user_id)
            return api_keys

    def toggle_api_key_revoked(self, key_id: int):
        with self.db_manager.get_session() as session:
            self.db_manager.toggle_api_key_revoked(session, key_id)
            session.commit()

    def get_similiar_artists(self, id: int, count: int = 5):
        with self.db_manager.get_session() as session:
            artist = self.db_manager.get_artist_by_id(session, id)
            if artist is None:
                return None
            artists = self.scrobblers[0].instance.get_similiar_artists(artist)
            db_artists = self.db_manager.get_artists_by_name(session, artists, count)
            return db_artists

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

    def get_user(self, username: str | None = None, user_id: int | None = None):
        with self.db_manager.get_session() as session:
            if username is not None:
                return self.db_manager.get_user_by_name(session, username)
            elif user_id is not None:
                return self.db_manager.get_user_by_id(session, user_id)
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

    def get_task(self, task_id: str) -> Task | None:
        task = self.task_queue.get(task_id)
        return task

    def post_task(self, func, task_id: str | None = None, *args, **kwargs):
        task_id = str(uuid4())[:8] if task_id is None else task_id
        self.task_queue[task_id] = Task()
        self.executor.submit(func, task_id, *args, **kwargs)
        return task_id

    def _update_task(self, task_id: str, **kwargs):
        task = self.task_queue[task_id]
        for k, v in kwargs.items():
            setattr(task, k, v)

    def save_object(
        self,
        session: Session,
        file_path: str,
        saving_path: str,
        file_size: int | None = None,
    ):
        file_size = os.path.getsize(file_path) if file_size is None else file_size
        best_storage = find_best_storage(self.storages, file_size)
        saved_object_path = best_storage.instance.save_file(file_path, saving_path)
        object_storage = ObjectStorageORM(
            link_type="storage",
            link_provider=best_storage.id,
            file_name=os.path.basename(saving_path),
            link=saved_object_path,
        )
        session.add(object_storage)
        session.flush()
        return object_storage

    def sync(self, task_id: str | None = None):
        task_id = self.post_task(self.sync_library, task_id)
        self.task_queue[task_id].result = SyncTaskResult()
        return task_id

    def sync_library(self, task_id: str):
        try:
            task: Task[SyncTaskResult] = self.task_queue[task_id]
            with self.db_manager.get_session() as session:
                db_files = self.db_manager.get_all_tracks_storage_links(session)
                storaged_files: set[tuple[str, str]] = set()
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
                    self.db_manager.bulk_delete_by_links(session, objects_for_deleting)
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
                        track_bytes = current_storage.get_range_bytes(
                            track.link, 0, 1024 * 1024 * 5
                        )["bytes"]
                        track_metadata = get_track_metadata_by_bytes(track_bytes)
                        self.add_new_track(session, track_metadata, track, storage.id)
                        task.result.tracks.processed += 1
                        task.result.tracks.added += 1
                    for cover in cover_to_adding.get(storage.id, []):
                        cover_link, cover_name = cover
                        entity = None
                        range_bytes: bytes = current_storage.get_range_bytes(
                            cover_link, 0, 99999999
                        )["bytes"]
                        cover_metadata = get_cover_metadata(
                            range_bytes,
                        )
                        if cover_metadata:
                            title = cover_metadata.get("title")
                            artists = cover_metadata.get("creator")
                            if title:
                                entity = self.db_manager.get_album_orm_by_title(
                                    session, title
                                )
                            elif artists and len(artists) == 1:
                                entity = self.db_manager.get_artist_orm_by_name(
                                    session, artists[0]
                                )
                        id_tuple = get_id_from_string(cover_name)
                        if id_tuple and not entity:
                            content_type, content_id = id_tuple[0]
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
                            task.result.unbound_files.covers.add(
                                (f"{storage.id}///{cover_link}", cover_name)
                            )
                            task.result.covers.processed += 1
                            continue
                        cover_storage = ObjectStorageORM(
                            link_type="storage",
                            link_provider=storage.id,
                            link=cover_link,
                            file_name=cover_name,
                        )
                        session.add(cover_storage)
                        session.flush()
                        entity.cover_path = cover_storage.id
                        session.flush()
                        task.result.covers.processed += 1
                        task.result.covers.added += 1
                    for lyrics in lyrics_to_adding.get(storage.id, []):
                        link, filename = lyrics
                        range_bytes: bytes = current_storage.get_range_bytes(
                            lyrics.link, 0, 9999999
                        )["bytes"]
                        decoded_text = range_bytes.decode()
                        lyrics_type, lyrics_text = read_lyrics_text(decoded_text)
                        name = filename.split(".")[0]
                        if lyrics_type == "lrc":
                            track = self.db_manager.get_track_by_name(
                                session, lyrics_text["title"]
                            )
                            if track is None:
                                track = track = self.db_manager.get_track_by_name(
                                    session, name
                                )
                            if track is None:
                                task.result.unbound_files.lyrics.add(
                                    (f"{storage.id}///{link}", filename)
                                )
                                task.result.lyrics.processed += 1
                                continue
                            new_lyrics = LyricsORM(
                                is_synced=True,
                                language="und",
                                synced_text=lyrics_text["text"],
                                offset=lyrics_text["offset"],
                                track_id=track.id,
                            )
                            session.add(new_lyrics)
                            session.flush()
                        elif lyrics_type == "txt":
                            track = self.db_manager.get_track_by_name(session, name)
                            if track is None:
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
                            link_type="storage",
                            link_provider=storage.id,
                            link=link,
                            lyrics_id=new_lyrics.id,
                            file_name=filename,
                        )
                        new_lyrics.path.append(lyrics_path)
                        session.add(lyrics_path)
                        session.flush()
                        task.result.lyrics.processed += 1
                        task.result.lyrics.added += 1
                    for video in videos_to_adding.get(storage.id, []):
                        link, filename = video
                        video_bytes = current_storage.get_range_bytes(
                            video.link, 0, 1024 * 1024 * 5
                        )["bytes"]
                        video_metadata = get_video_metadata(video_bytes)
                        video_title = video_metadata.get("title")
                        if video_title is None:
                            video_title = filename.rsplit(".", 1)[0]
                        track = self.db_manager.get_track_by_name(session, video_title)
                        if track is None:
                            id_tuple = get_id_from_string(filename, "tr")
                            if id_tuple:
                                track = self.db_manager.get_track_by_id(
                                    session, id_tuple[1]
                                )
                        if track is None:
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
                            link_type="storage",
                            link_provider=storage.id,
                            link=link,
                            file_name=filename,
                        )
                        music_video.local_link.append(video_storage)
                        session.add(music_video)
                        session.flush()
                        task.result.videos.processed += 1
                        task.result.videos.added += 1
                self.db_manager.delete_orphans(session)
                session.commit()
                self._update_task(task_id, status="finished")
                self.logger.info("Syncing succesful completed")
        except Exception as e:
            self._update_task(task_id, status="error", error=str(e))
            self.logger.warning(
                "Problem in library syncing", task_id=task_id, error=str(e)
            )

    def import_library(
        self,
        task_id: str | None = None,
        importer_tag: str | None = None,
        user_id: int | None = None,
    ):
        task_id = self.post_task(
            func=self.import_tracks,
            task_id=task_id,
            importer_tag=importer_tag,
            user_id=user_id,
        )
        self.task_queue[task_id].result = ImportTaskResult()
        return task_id

    def import_tracks(
        self, task_id: str, importer_tag: str, user_id: int | None = None
    ):
        task: Task[ImportTaskResult] = self.task_queue[task_id]
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
            task.result.tracks.searched = len(favorited_tracks)
            task.result.albums.searched = len(favorited_albums)
            task.result.artists.searched = len(favorited_artists)
            task.result.playlists.searched = len(favorited_playlists)
            unique_tracks_ids = {*favorited_tracks}
            unique_albums_ids = {*favorited_albums}
            unique_artists_ids = {*favorited_artists}
            unique_playlists_ids = {*favorited_playlists}
            playlist_tracks_to_add: list[tuple[int, list[ImporterPlaylistTrack]]] = []
            artist_map: dict[int | str, int] = {}
            album_map: dict[int | str, int] = {}
            track_map: dict[int | str, int] = {}
            tracks_with_lyrics = []
            tracks_with_music_videos = []
            album_artist_link = {}
            unique_playlists_ids.update(selected_importer.get_user_playlists())
            task.result.playlists.searched = len(unique_playlists_ids)
            dst = self.temp_dir

            for playlist_id in unique_playlists_ids:
                try:
                    playlist_info = selected_importer.get_playlist(playlist_id)
                    unique_tracks_ids.update(
                        [track.id for track in playlist_info.tracks]
                    )
                    task.result.tracks.searched = len(unique_tracks_ids)
                    db_playlist = PlaylistORM(name=playlist_info.title, is_public=False)
                    session.add(db_playlist)
                    session.flush()
                    playlist_owner = PlaylistOwnerORM(
                        owner_id=user_id, playlist_id=db_playlist.id
                    )
                    session.add(playlist_owner)
                    session.flush()
                    task.result.playlists.saved += 1
                    playlist_tracks_to_add.append(
                        (db_playlist.id, playlist_info.tracks)
                    )
                    if playlist_info.cover_uri:
                        cover_path = dst / f"pl-{db_playlist.id}.jpg"
                        task.result.covers.searched += 1
                        save_file_from_url(playlist_info.cover_uri, cover_path)
                        with open(cover_path, "rb") as f:
                            ext = image_mime(f.read(20)).split("/")[1]
                        cover_name = f"pl-{db_playlist.id}.{ext}"
                        cover_object = self.save_object(
                            session,
                            str(cover_path),
                            cover_name,
                        )
                        task.result.covers.saved += 1
                        db_playlist.cover_path = cover_object.id
                        session.flush()
                    session.commit()
                except Exception as e:
                    session.rollback()
                    self.logger.warning(
                        "Problem in importing playlist",
                        importer=importer_tag,
                        user_id=user_id,
                        playlist_id=playlist_id,
                        error=str(e),
                    )

            for track_id in unique_tracks_ids:
                try:
                    if track_id is None:
                        continue
                    track_info = selected_importer.get_track(track_id)
                    if track_info.has_lyrics:
                        tracks_with_lyrics.append(track_id)
                        task.result.lyrics.searched += 1
                    if track_info.has_video:
                        tracks_with_music_videos.append(track_id)
                        task.result.videos.searched += 1
                    unique_albums_ids.update(track_info.album_ids)
                    task.result.albums.searched = len(unique_albums_ids)
                    unique_artists_ids.update(track_info.artist_ids)
                    task.result.artists.searched = len(unique_artists_ids)
                    url, name = selected_importer.get_track_download_link(track_id)
                    track_dst = dst / name
                    save_file_from_url(url, track_dst)
                    write_track_metadata(
                        str(track_dst),
                        {
                            "title": [track_info.title],
                            "artist": track_info.artists,
                            "album": [track_info.albums[0].title],
                            "albumartist": track_info.albums[0].album_artists,
                            "tracknumber": [str(track_info.albums[0].album_position)],
                            "discnumber": [str(track_info.albums[0].disc_number)],
                            "date": [str(track_info.year)],
                            "genre": track_info.genres,
                            "mood": track_info.moods,
                        },
                    )
                    sanitized_name = (
                        f"{sanitize_filename(track_info.title)}.{name.split('.')[1]}"
                    )
                    saving_path = Path(
                        (
                            f"{sanitize_filename(track_info.artists[0])}/{sanitize_filename(track_info.albums[0].title)}/{sanitized_name}"
                        )
                    )
                    best_storage = find_best_storage(
                        self.storages,
                        track_dst.stat().st_size,
                    )
                    saved_path = best_storage.instance.save_file(track_dst, saving_path)
                    task.result.tracks.saved += 1
                    db_track_id = self.add_new_track(
                        session,
                        TrackMetadata(
                            title=track_info.title,
                            artists=track_info.artists,
                            albums=track_info.albums,
                            year=track_info.year,
                            length=track_info.length,
                            bpm=track_info.bpm,
                            genres=track_info.genres,
                            moods=track_info.moods,
                        ),
                        FilePathInfo(link=saved_path, filename=sanitized_name),
                        best_storage.id,
                    )
                    track_map[track_id] = db_track_id
                    session.commit()
                except Exception as e:
                    session.rollback()
                    self.logger.warning(
                        "Problem in importing track",
                        importer=importer_tag,
                        user_id=user_id,
                        track_id=track_id,
                        error=str(e),
                    )

            for album_id in unique_albums_ids:
                try:
                    if album_id is None:
                        continue
                    album = selected_importer.get_album(album_id)
                    unique_artists_ids.update(album.artist_ids)
                    db_album = self.db_manager.find_or_create_album(
                        session,
                        album.title,
                        artists_names=album.artists,
                        year=album.year,
                        type=album.album_type,
                        description=album.description,
                    )
                    task.result.albums.saved += 1
                    album_map[album_id] = db_album.id
                    if album.cover_uri:
                        task.result.covers.searched += 1
                        sanitized_title = sanitize_filename(db_album.title)
                        cover_path = dst / f"al-{db_album.id}.jpg"
                        save_file_from_url(album.cover_uri, cover_path)
                        try:
                            write_cover_metadata(
                                str(cover_path),
                                album=album.title,
                                artists=album.artists,
                                genres=album.genres,
                            )
                        except Exception as e:
                            self.logger.warning(
                                "Problem in writing imported cover metadata",
                                importer=importer_tag,
                                user_id=user_id,
                                album_id=album_id,
                                cover_path=str(cover_path),
                                error=str(e),
                            )
                        with open(cover_path, "rb") as f:
                            ext = image_mime(f.read(20)).split("/")[1]
                        cover_object = self.save_object(
                            session,
                            str(cover_path),
                            f"{sanitize_filename(album.artists[0])}/{sanitized_title}/{sanitized_title}.{ext}",
                        )
                        task.result.covers.saved += 1
                        db_album.cover_path = cover_object.id
                        session.flush()
                    genre_links = []
                    for genre in album.genres:
                        db_genre = self.db_manager.find_or_create_genre(session, genre)
                        exists = session.exec(
                            select(AlbumGenreLink).where(
                                AlbumGenreLink.album_id == db_album.id,
                                AlbumGenreLink.genre_id == db_genre.id,
                            )
                        ).first()

                        if not exists:
                            session.add(
                                AlbumGenreLink(
                                    album_id=db_album.id, genre_id=db_genre.id
                                )
                            )
                    session.add_all(genre_links)
                    session.commit()
                    for artist_id in album.artist_ids:
                        if artist_id in album_artist_link:
                            album_artist_link[artist_id].add(db_album.id)
                        else:
                            album_artist_link[artist_id] = {db_album.id}

                except Exception as e:
                    session.rollback()
                    self.logger.warning(
                        "Problem in importing album",
                        importer=importer_tag,
                        user_id=user_id,
                        album_id=album_id,
                        error=str(e),
                    )

            for artist_id in unique_artists_ids:
                try:
                    if artist_id is None:
                        continue
                    artist = selected_importer.get_artist(artist_id)

                    db_artist = self.db_manager.find_or_create_artist(
                        session, artist.name
                    )
                    artist_map[artist_id] = db_artist.id
                    task.result.artists.saved += 1
                    db_artist.description = artist.description
                    db_album_artist_links = []
                    for album_id in album_artist_link.get(artist_id, {}):
                        exists = session.exec(
                            select(AlbumArtistLink).where(
                                AlbumArtistLink.album_id == album_id,
                                AlbumArtistLink.artist_id == db_artist.id,
                            )
                        ).first()

                        if not exists:
                            db_album_artist_links.append(
                                AlbumArtistLink(
                                    album_id=album_id, artist_id=db_artist.id
                                )
                            )
                    session.add_all(db_album_artist_links)
                    session.commit()
                    if artist.cover_uri:
                        task.result.covers.searched += 1
                        sanitized_name = sanitize_filename(artist.name)
                        cover_path = dst / f"ar-{db_artist.id}.jpg"
                        save_file_from_url(artist.cover_uri, cover_path)
                        try:
                            write_cover_metadata(
                                str(cover_path),
                                artists=[artist.name],
                                genres=artist.genres,
                            )
                        except Exception as e:
                            self.logger.warning(
                                "Problem in writing imported cover metadata",
                                importer=importer_tag,
                                user_id=user_id,
                                artist_id=artist_id,
                                cover_path=str(cover_path),
                                error=str(e),
                            )
                        with open(cover_path, "rb") as f:
                            ext = image_mime(f.read(20)).split("/")[1]
                        cover_object = self.save_object(
                            session,
                            str(cover_path),
                            f"{sanitized_name}/{sanitized_name}.{ext}",
                        )
                        task.result.covers.saved += 1
                        db_artist.cover_path = cover_object.id
                        session.add(db_artist)
                        session.flush()
                    for genre in artist.genres:
                        db_genre = self.db_manager.find_or_create_genre(session, genre)
                        exists = session.exec(
                            select(ArtistGenreLink).where(
                                ArtistGenreLink.artist_id == db_artist.id,
                                ArtistGenreLink.genre_id == db_genre.id,
                            )
                        ).first()

                        if not exists:
                            session.add(
                                ArtistGenreLink(
                                    artist_id=db_artist.id, genre_id=db_genre.id
                                )
                            )
                    session.commit()
                except Exception as e:
                    session.rollback()
                    self.logger.warning(
                        "Problem in importing artist",
                        importer=importer_tag,
                        user_id=user_id,
                        artist_id=artist_id,
                        error=str(e),
                    )

            for playlist_entry in playlist_tracks_to_add:
                playlist_id, tracks = playlist_entry
                try:
                    for track in tracks:
                        if track.id in track_map:
                            link = PlaylistTrackLink(
                                playlist_id=playlist_id,
                                track_id=track_map[track.id],
                                position=track.playlist_position,
                            )
                            session.add(link)
                            session.commit()
                except Exception as e:
                    session.rollback()
                    self.logger.warning(
                        "Problem in importing playlist",
                        importer=importer_tag,
                        user_id=user_id,
                        playlist_id=playlist_id,
                        error=str(e),
                    )

            for track_id in tracks_with_lyrics:
                try:
                    track = self.db_manager.get_track_by_id(
                        session, track_map[track_id]
                    )
                    if track is None:
                        continue
                    url, name = selected_importer.get_lyrics_download_link(track_id)

                    saved_path = dst / sanitize_filename(name)
                    save_file_from_url(url, saved_path)
                    text = saved_path.read_text(encoding="utf-8")
                    lyrics_type, lyrics_content = read_lyrics_text(text)
                    if lyrics_type == "lrc":
                        new_lyrics = LyricsORM(
                            is_synced=True,
                            language="und",
                            synced_text=lyrics_content["text"],
                            offset=lyrics_content["offset"],
                            track_id=track.id,
                        )
                        session.add(new_lyrics)
                    else:
                        new_lyrics = LyricsORM(
                            is_synced=False,
                            language="und",
                            plain_text=lyrics_content,
                            track_id=track.id,
                        )
                        session.add(new_lyrics)
                    saving_path = f"{sanitize_filename(track.artists[0].name)}/{sanitize_filename(track.albums[0].title)}/{sanitize_filename(track.title)}.{lyrics_type}"
                    lyrics_object = self.save_object(
                        session, str(saved_path), saving_path
                    )
                    task.result.lyrics.saved += 1
                    new_lyrics.path.append(lyrics_object)
                    session.add(lyrics_object)
                    session.commit()
                except Exception as e:
                    session.rollback()
                    self.logger.warning(
                        "Problem in importing track lyrics",
                        importer=importer_tag,
                        user_id=user_id,
                        track_id=track_id,
                        error=str(e),
                    )

            for track_id in tracks_with_music_videos:
                try:
                    track = self.db_manager.get_track_by_id(
                        session, track_map[track_id]
                    )
                    if track is None:
                        continue
                    url, name = selected_importer.get_music_video_download_link(
                        track_id
                    )
                    video_dst = dst / sanitize_filename(name)
                    save_file_from_url(url, video_dst)
                    write_video_metadata(
                        ",".join(artist.name for artist in track.artists),
                        ",".join(album.title for album in track.albums),
                        track.title,
                        video_dst,
                    )
                    music_video = MusicVideoORM(track_id=track.id)
                    session.add(music_video)
                    session.flush()
                    splitted_name = name.rsplit(".", 1)
                    ext = (
                        splitted_name[1]
                        if len(splitted_name) > 1 and splitted_name[1]
                        else "mp4"
                    )
                    saving_path = f"{sanitize_filename(track.artists[0].name)}/{sanitize_filename(track.albums[0].title)}/{sanitize_filename(track.title)}.{ext}"
                    video_object = self.save_object(
                        session, str(video_dst), saving_path
                    )
                    task.result.videos.saved += 1
                    music_video.local_link.append(video_object)
                    session.add(video_object)
                    session.commit()
                except Exception as e:
                    session.rollback()
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
            self._update_task(task_id, status="finished")
            self.logger.info(
                "Succesful imported library", importer=importer_tag, user_id=user_id
            )

    def check_status(self):
        return ServicesStatus(
            downloaders=[
                *_get_runtime_errors(self.downloaders),
                *self.start_errors.downloaders,
            ],
            importers=[
                *_get_runtime_errors(self.importers),
                *self.start_errors.importers,
            ],
            scrobblers=[
                *_get_runtime_errors(self.scrobblers),
                *self.start_errors.scrobblers,
            ],
            search=[
                *_get_runtime_errors(self.search_engines),
                *self.start_errors.search,
            ],
            storages=[*_get_runtime_errors(self.storages), *self.start_errors.storages],
        )

    def get_library_stats(self):
        with self.db_manager.get_session() as session:
            tracks_total = self.db_manager.get_model_count(session, TrackORM)
            tracks_with_lyrics = self.db_manager.get_count_with_lyrics(session)
            tracks_with_videos = self.db_manager.get_count_with_videos(session)

            albums_total = self.db_manager.get_model_count(session, AlbumORM)
            albums_with_cover = self.db_manager.get_count_with_cover(session, AlbumORM)

            artists_total = self.db_manager.get_model_count(session, ArtistORM)
            artists_with_cover = self.db_manager.get_count_with_cover(
                session, ArtistORM
            )

            lyrics_total = self.db_manager.get_model_count(session, LyricsORM)
            videos_total = self.db_manager.get_model_count(session, MusicVideoORM)
            genre_count, tracks_genre, albums_genre, artists_genre = (
                self.db_manager.get_genre_counts(session)
            )
            mood_count, tracks_moods = self.db_manager.get_moods_counts(session)
            return LibraryStats(
                tracks_total=tracks_total,
                tracks_with_lyrics=tracks_with_lyrics,
                tracks_with_videos=tracks_with_videos,
                albums_total=albums_total,
                albums_with_cover=albums_with_cover,
                artists_total=artists_total,
                artists_with_cover=artists_with_cover,
                lyrics_total=lyrics_total,
                videos_total=videos_total,
                genres_total=genre_count,
                artists_with_genres=artists_genre,
                albums_with_genres=albums_genre,
                tracks_with_genres=tracks_genre,
                moods_total=mood_count,
                tracks_with_moods=tracks_moods,
            )
