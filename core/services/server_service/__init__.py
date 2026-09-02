from core.db.models import TrackORM, AlbumORM, ArtistORM, LyricsORM, MusicVideoORM
from core.services import (
    album_service,
    artist_service,
    track_service,
)
from core.schemas import SearchResults, ServicesStatus, LibraryStats, ObjectStorage
from sqlmodel import Session
from core.services.server_service import server_repository


def local_search(
    session: Session,
    query: str,
    artistCount: int,
    artistOffset: int,
    albumCount: int,
    albumOffset: int,
    songCount: int,
    songOffset: int,
) -> SearchResults:
    return SearchResults(
        artists=artist_service.search_artists(
            session, query, artistCount, artistOffset
        ),
        albums=album_service.search_albums(session, query, albumCount, albumOffset),
        tracks=track_service.search_tracks(session, query, songCount, songOffset),
    )


def bulk_delete_by_links(
    session: Session, provider_links: list[tuple[str, str]]
) -> tuple[int, int, int, int]:
    return server_repository.bulk_delete_by_links(session, provider_links)


def delete_orphans(session: Session) -> tuple[int, int, int]:
    return server_repository.delete_orphans(session)


def get_storage_object_by_id(session: Session, object_id: int) -> ObjectStorage | None:
    return server_repository.get_storage_object_by_id(session, object_id)


def check_status() -> ServicesStatus:
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


def get_library_stats(session: Session) -> LibraryStats:
    tracks_total = server_repository.get_model_count(session, TrackORM)
    tracks_with_lyrics = server_repository.get_count_with_lyrics(session)
    tracks_with_videos = server_repository.get_count_with_videos(session)
    albums_total = server_repository.get_model_count(session, AlbumORM)
    albums_with_cover = server_repository.get_count_with_cover(session, AlbumORM)
    artists_total = server_repository.get_model_count(session, ArtistORM)
    artists_with_cover = server_repository.get_count_with_cover(session, ArtistORM)
    lyrics_total = server_repository.get_model_count(session, LyricsORM)
    videos_total = server_repository.get_model_count(session, MusicVideoORM)
    genre_count, tracks_genre, albums_genre, artists_genre = (
        server_repository.get_genre_counts(session)
    )
    mood_count, tracks_moods = server_repository.get_moods_counts(session)
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
