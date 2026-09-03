from pathlib import Path
from core.db.manager import DBManager
from core.modules.importers.loader import load_importers
from core.tasks.tasks_manager import TasksManager
from core.tasks.schemas import Task, ImportTaskResult
from sqlmodel import select
from core.schemas import LRCLyrics, TrackMetadata, FilePathInfo
from core.utils import (
    sanitize_filename,
    save_file_from_url,
    write_video_metadata,
    read_lyrics_text,
    image_mime,
    write_cover_metadata,
    write_track_metadata,
)
from core.errors import BaseError
from core.modules.storages.storages_manager import StoragesManager
from core.modules.importers.schemas import ImporterPlaylistTrack
from core.db.models import (
    StarredArtist,
    StarredAlbum,
    StarredTrack,
    LyricsORM,
    MusicVideoORM,
    PlaylistTrackLink,
    ArtistGenreLink,
    AlbumArtistLink,
    AlbumGenreLink,
    PlaylistOwnerORM,
    PlaylistORM,
)
from core.services import (
    album_service,
    artist_service,
    track_service,
    user_service,
)


class _ImportersManager:
    def __init__(self):
        self.config = dict()
        # self.temp_dir = self.config["temp_dir"]
        self.importers, _ = load_importers(self.config)

    def import_tracks(
        self, task_id: str, importer_tag: str, user_id: int | None = None
    ):
        task: Task[ImportTaskResult] = TasksManager.task_queue.importing[task_id]
        importers = self.importers
        selected_importer = None
        for importer in importers:
            if importer.tag == importer_tag:
                selected_importer = importer.instance
                break
        if selected_importer is None:
            return
        with DBManager.get_session() as session:
            (
                favorited_tracks,
                favorited_albums,
                favorited_artists,
                favorited_playlists,
            ) = selected_importer.get_favorited()
            if user_id:
                owner = user_service.get_user_by_id(session, user_id)
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
            # dst = self.temp_dir
            dst = Path("test")
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
                        cover_object = StoragesManager.save_object(
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
                    # self.logger.warning(
                    #    "Problem in importing playlist",
                    #    importer=importer_tag,
                    #    user_id=user_id,
                    #    playlist_id=playlist_id,
                    #    error=str(e),
                    # )

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
                    saving_path = f"{sanitize_filename(track_info.artists[0])}/{sanitize_filename(track_info.albums[0].title)}/{sanitized_name}"

                    best_storage = StoragesManager.find_best_storage(
                        track_dst.stat().st_size,
                    )
                    saved_path = best_storage.instance.save_file(track_dst, saving_path)
                    task.result.tracks.saved += 1
                    db_track_id = track_service.add_new_track(
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
                    # self.logger.warning(
                    #    "Problem in importing track",
                    #    importer=importer_tag,
                    #    user_id=user_id,
                    #    track_id=track_id,
                    #    error=str(e),
                    # )

            for album_id in unique_albums_ids:
                try:
                    if album_id is None:
                        continue
                    album = selected_importer.get_album(album_id)
                    unique_artists_ids.update(album.artist_ids)
                    db_album = album_service.find_or_create_album(
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
                            pass
                            # self.logger.warning(
                            #    "Problem in writing imported cover metadata",
                            #    importer=importer_tag,
                            #    user_id=user_id,
                            #    album_id=album_id,
                            #    cover_path=str(cover_path),
                            #    error=str(e),
                            # )
                        with open(cover_path, "rb") as f:
                            ext = image_mime(f.read(20)).split("/")[1]
                        cover_object = StoragesManager.save_object(
                            session,
                            str(cover_path),
                            f"{sanitize_filename(album.artists[0])}/{sanitized_title}/{sanitized_title}.{ext}",
                        )
                        task.result.covers.saved += 1
                        db_album.cover_path = cover_object.id
                        session.flush()
                    genre_links = []
                    for genre in album.genres:
                        db_genre = track_service.find_or_create_genre(session, genre)
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
                    # self.logger.warning(
                    #    "Problem in importing album",
                    #    importer=importer_tag,
                    #    user_id=user_id,
                    #    album_id=album_id,
                    #    error=str(e),
                    # )

            for artist_id in unique_artists_ids:
                try:
                    if artist_id is None:
                        continue
                    artist = selected_importer.get_artist(artist_id)

                    db_artist = artist_service.find_or_create_artist(
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
                            pass
                            # self.logger.warning(
                            #    "Problem in writing imported cover metadata",
                            #    importer=importer_tag,
                            #    user_id=user_id,
                            #    artist_id=artist_id,
                            #    cover_path=str(cover_path),
                            #    error=str(e),
                            # )
                        with open(cover_path, "rb") as f:
                            ext = image_mime(f.read(20)).split("/")[1]
                        cover_object = StoragesManager.save_object(
                            session,
                            str(cover_path),
                            f"{sanitized_name}/{sanitized_name}.{ext}",
                        )
                        task.result.covers.saved += 1
                        db_artist.cover_path = cover_object.id
                        session.add(db_artist)
                        session.flush()
                    for genre in artist.genres:
                        db_genre = track_service.find_or_create_genre(session, genre)
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
                    # self.logger.warning(
                    #    "Problem in importing artist",
                    #    importer=importer_tag,
                    #    user_id=user_id,
                    #    artist_id=artist_id,
                    #    error=str(e),
                    # )

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
                    # self.logger.warning(
                    #    "Problem in importing playlist",
                    #    importer=importer_tag,
                    #    user_id=user_id,
                    #    playlist_id=playlist_id,
                    #    error=str(e),
                    # )

            for track_id in tracks_with_lyrics:
                try:
                    track = track_service.get_track_by_id(session, track_map[track_id])
                    if isinstance(track, BaseError):
                        continue
                    url, name = selected_importer.get_lyrics_download_link(track_id)

                    saved_path = dst / sanitize_filename(name)
                    save_file_from_url(url, saved_path)
                    text = saved_path.read_text(encoding="utf-8")
                    lyrics_content = read_lyrics_text(text)
                    lyrics_type = ""
                    if isinstance(lyrics_content, LRCLyrics):
                        lyrics_type = "lrc"
                        new_lyrics = LyricsORM(
                            is_synced=True,
                            language="und",
                            synced_text=lyrics_content.text,
                            offset=lyrics_content.offset,
                            track_id=track.id,
                        )
                        session.add(new_lyrics)
                    else:
                        lyrics_type = "txt"
                        new_lyrics = LyricsORM(
                            is_synced=False,
                            language="und",
                            plain_text=lyrics_content,
                            track_id=track.id,
                        )
                        session.add(new_lyrics)
                    saving_path = f"{sanitize_filename(track.artists[0].name)}/{sanitize_filename(track.albums[0].title)}/{sanitize_filename(track.title)}.{lyrics_type}"
                    lyrics_object = StoragesManager.save_object(
                        session, str(saved_path), saving_path
                    )
                    task.result.lyrics.saved += 1
                    new_lyrics.path.append(lyrics_object)
                    session.add(lyrics_object)
                    session.commit()
                except Exception as e:
                    session.rollback()
                    # self.logger.warning(
                    #    "Problem in importing track lyrics",
                    #    importer=importer_tag,
                    #    user_id=user_id,
                    #    track_id=track_id,
                    #    error=str(e),
                    # )

            for track_id in tracks_with_music_videos:
                try:
                    track = track_service.get_track_by_id(session, track_map[track_id])
                    if isinstance(track, BaseError):
                        return track
                    url, name = selected_importer.get_music_video_download_link(
                        track_id
                    )
                    video_dst = dst / sanitize_filename(name)
                    save_file_from_url(url, video_dst)
                    write_video_metadata(
                        ",".join(artist.name for artist in track.artists),
                        ",".join(album.title for album in track.albums),
                        track.title,
                        str(video_dst),
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
                    video_object = StoragesManager.save_object(
                        session, str(video_dst), saving_path
                    )
                    task.result.videos.saved += 1
                    music_video.local_link.append(video_object)
                    session.add(video_object)
                    session.commit()
                except Exception as e:
                    session.rollback()
                    # self.logger.warning(
                    #    "Problem in adding imported music video",
                    #    importer=importer_tag,
                    #    user_id=user_id,
                    #    track_id=track_id,
                    #    error=str(e),
                    # )

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
            TasksManager.task_queue.importing[task_id].status = "finished"
            # self.logger.info(
            #    "Succesful imported library", importer=importer_tag, user_id=user_id
            # )


ImportersManager = _ImportersManager()
