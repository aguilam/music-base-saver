from sqlalchemy import tuple_, func, distinct
from core.db.mappers import object_storage_from_orm
from core.schemas import ObjectStorage
from core.db.models import (
    AlbumORM,
    ArtistORM,
    TrackAlbumLink,
    TrackORM,
    ObjectStorageORM,
    AudioFileORM,
    LyricsORM,
    MusicVideoORM,
    GenreORM,
    TrackGenreLink,
    AlbumGenreLink,
    ArtistGenreLink,
    MoodORM,
    TrackMoodLink,
    AlbumArtistLink,
    TrackArtistsLink,
)
from sqlmodel import select, col, Session, delete


def get_storage_object_by_id(session: Session, id: int) -> ObjectStorage | None:
    storage = session.exec(
        select(ObjectStorageORM).where(ObjectStorageORM.id == id)
    ).first()
    return object_storage_from_orm(storage) if storage else None


def bulk_delete_by_links(
    session: Session, provider_link: list[tuple[str, str]]
) -> tuple[int, int, int, int]:
    select_ids = select(
        ObjectStorageORM.id,
        ObjectStorageORM.audio_id,
        ObjectStorageORM.lyrics_id,
        ObjectStorageORM.music_video_id,
    ).where(
        tuple_(col(ObjectStorageORM.link_provider), col(ObjectStorageORM.link)).in_(
            provider_link
        )
    )
    ids_statement = session.exec(select_ids).all()
    links_ids = [r[0] for r in ids_statement]
    audio_ids = [r[1] for r in ids_statement]
    lyrics_ids = [r[2] for r in ids_statement]
    videos_ids = [r[3] for r in ids_statement]
    covers_links_count = (
        session.exec(
            select(func.count(ObjectStorageORM.id)).where(
                col(ObjectStorageORM.id).in_(links_ids),
                col(ObjectStorageORM.audio_id).is_(None),
                col(ObjectStorageORM.lyrics_id).is_(None),
                col(ObjectStorageORM.music_video_id).is_(None),
            )
        ).one()
        or 0
    )
    session.exec(
        delete(ObjectStorageORM).where(col(ObjectStorageORM.id).in_(links_ids))
    )
    session.flush()
    audio_statement = select(AudioFileORM).where(col(AudioFileORM.id).in_(audio_ids))
    searched_audios = session.exec(audio_statement).all()
    audios_for_deleting = []
    for audio in searched_audios:
        if len(audio.links) == 0:
            audios_for_deleting.append(audio.id)
    deleted_audio = session.exec(
        delete(AudioFileORM).where(col(AudioFileORM.id).in_(audios_for_deleting))
    )
    searched_lyrics = session.exec(
        select(LyricsORM).where(col(LyricsORM.id).in_(lyrics_ids))
    ).all()
    lyrics_for_deleting = []
    for lyrics in searched_lyrics:
        if len(lyrics.path) == 0:
            lyrics_for_deleting.append(lyrics.id)
    deleted_lyrics = session.exec(
        delete(LyricsORM).where(col(LyricsORM.id).in_(lyrics_for_deleting))
    )
    searched_videos = session.exec(
        select(MusicVideoORM).where(col(MusicVideoORM.id).in_(videos_ids))
    ).all()
    videos_for_deleting = []
    for video in searched_videos:
        if len(video.local_link) == 0:
            videos_for_deleting.append(video.id)
    deleted_videos = session.exec(
        delete(MusicVideoORM).where(col(MusicVideoORM.id).in_(videos_for_deleting))
    )
    session.commit()
    return (
        deleted_audio.rowcount,
        covers_links_count,
        deleted_lyrics.rowcount,
        deleted_videos.rowcount,
    )


def get_model_count(session: Session, model) -> int:
    model_count = session.scalar(select(func.count(model.id))) or 0
    return model_count


def get_genre_counts(session: Session) -> tuple[int, int, int, int]:
    genre_count: int = session.scalar(select(func.count(GenreORM.id))) or 0
    tracks_genre: int = (
        session.scalar(select(func.count(distinct(col(TrackGenreLink.track_id))))) or 0
    )
    albums_genre: int = (
        session.scalar(select(func.count(distinct(col(AlbumGenreLink.album_id))))) or 0
    )
    artists_genre: int = (
        session.scalar(select(func.count(distinct(col(ArtistGenreLink.artist_id)))))
        or 0
    )
    return (genre_count, tracks_genre, albums_genre, artists_genre)


def get_moods_counts(session: Session) -> tuple[int, int]:
    mood_count: int = session.scalar(select(func.count(MoodORM.id))) or 0
    tracks_moods: int = (
        session.scalar(select(func.count(distinct(col(TrackMoodLink.track_id))))) or 0
    )
    return (mood_count, tracks_moods)


def get_count_with_lyrics(session: Session) -> int:
    tracks_count: int = (
        session.scalar(
            select(func.count(TrackORM.id)).where(col(TrackORM.lyrics).any())
        )
        or 0
    )
    return tracks_count


def get_count_with_videos(session: Session) -> int:
    tracks_count: int = (
        session.scalar(
            select(func.count(TrackORM.id)).where(col(TrackORM.music_videos).any())
        )
        or 0
    )
    return tracks_count


def get_count_with_cover(session: Session, model) -> int:
    model_count = (
        session.scalar(
            select(func.count(model.id)).where(model.cover_path.is_not(None))
        )
        or 0
    )
    return model_count


def delete_orphans(session: Session) -> tuple[int, int, int]:
    deleted_tracks = session.exec(
        delete(TrackORM).where(
            col(TrackORM.id).not_in(
                select(AudioFileORM.track_id).where(
                    col(AudioFileORM.track_id).is_not(None)
                )
            )
        )
    )
    session.flush()

    deleted_albums = session.exec(
        delete(AlbumORM).where(col(AlbumORM.id).not_in(select(TrackAlbumLink.album_id)))
    )

    session.flush()
    deleted_artists = session.exec(
        delete(ArtistORM).where(
            col(ArtistORM.id).not_in(select(AlbumArtistLink.artist_id)),
            col(ArtistORM.id).not_in(select(TrackArtistsLink.artist_id)),
            col(ArtistORM.id).not_in(
                select(AlbumArtistLink.artist_id).where(
                    col(AlbumArtistLink.album_id).is_not(None)
                )
            ),
            col(ArtistORM.id).not_in(
                select(TrackArtistsLink.artist_id).where(
                    col(TrackArtistsLink.track_id).is_not(None)
                )
            ),
        )
    )
    session.flush()

    return (
        deleted_tracks.rowcount,
        deleted_albums.rowcount,
        deleted_artists.rowcount,
    )
