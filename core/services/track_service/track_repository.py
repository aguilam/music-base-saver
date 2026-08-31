from core.utils.utils import decode_datetime_cursor, encode_datetime_cursor
from core.db.mappers import (
    track_from_orm,
    track_short_from_orm,
    mood_from_orm,
    genre_from_orm,
    music_video_from_orm,
)
from core.schemas import Track, TrackShort, Mood, Genre, MusicVideo
from core.errors import NotFoundError, BaseError
from core.db.utils import in_load_typing
from sqlalchemy import or_, and_
from sqlalchemy.orm import selectinload
from sqlmodel import select, col, Session, literal
from core.db.models import (
    TrackORM,
    ArtistORM,
    AlbumORM,
    TrackAlbumLink,
    ObjectStorageORM,
    MoodORM,
    GenreORM,
    MusicVideoORM,
)


def find_track(
    session: Session,
    title: str,
    album_title: str | None = None,
    artists: list[str] | None = None,
) -> Track | BaseError:
    normalized_title = title.strip().lower()
    stmt = select(TrackORM).where(TrackORM.normalized_title == normalized_title)
    if album_title:
        normalized_album = album_title.strip().lower()
        stmt.join(col(TrackORM.albums_links)).where(
            TrackAlbumLink.album.normalized_title == normalized_album
        ).distinct()
    if artists:
        normalized_names = [name.strip().lower() for name in artists]
        stmt.join(col(TrackORM.artists)).where(
            col(ArtistORM.normalized_name).in_(normalized_names)
        ).distinct()
    track = session.exec(stmt).first()
    return track_from_orm(track) if track else NotFoundError()


def get_all_tracks(session: Session) -> list[TrackShort]:
    statement = select(TrackORM).options(selectinload(in_load_typing(TrackORM.files)))
    orm_tracks = session.exec(statement).all()
    return [track_short_from_orm(track) for track in orm_tracks]


def get_track_by_id(session: Session, id: int) -> Track | BaseError:
    statement = (
        select(TrackORM)
        .where(TrackORM.id == id)
        .options(
            selectinload(in_load_typing(TrackORM.files)),
            selectinload(in_load_typing(TrackORM.artists)),
            selectinload(in_load_typing(TrackORM.lyrics)),
            selectinload(in_load_typing(TrackORM.music_videos)),
            selectinload(in_load_typing(TrackORM.albums_links)).selectinload(
                in_load_typing(TrackAlbumLink.album)
            ),
        )
    )
    orm_track = session.exec(statement).first()
    return track_from_orm(orm_track) if orm_track else NotFoundError()


def get_track_by_name(session: Session, title: str) -> Track | BaseError:
    orm_track = session.exec(
        select(TrackORM).where(col(TrackORM.title).ilike(title))
    ).first()
    return track_from_orm(orm_track) if orm_track else NotFoundError()


def get_track_cursor(
    session: Session, limit: int, cursor: str | None
) -> tuple[list[TrackShort], str | None]:
    last_id, created_at = decode_datetime_cursor(cursor) if cursor else (None, None)
    statement = (
        select(TrackORM)
        .order_by(col(TrackORM.created_at).desc(), col(TrackORM.id).desc())
        .limit(limit + 1)
    )
    if last_id is not None and created_at is not None:
        statement = statement.where(
            or_(
                col(TrackORM.created_at) < created_at,
                and_(
                    col(TrackORM.created_at) == created_at,
                    col(TrackORM.id) < last_id,
                ),
            )
        )
    tracks = list(session.exec(statement).all())
    next_cursor = None
    if len(tracks) > limit:
        tracks.pop()
        last_item = tracks[-1]
        next_cursor = encode_datetime_cursor(last_item.id, last_item.created_at)
    return [track_short_from_orm(track) for track in tracks], next_cursor


def get_all_tracks_storage_links(session: Session) -> set[tuple[str, str]]:
    combined = (
        ObjectStorageORM.link_provider + literal("///") + ObjectStorageORM.link
    ).label("combined")
    statement = select(combined, ObjectStorageORM.file_name).where(
        ObjectStorageORM.link_type == "storage"
    )
    result = session.exec(statement).all()
    return set(result)


def get_moods(session: Session) -> list[Mood]:
    moods = session.exec(
        select(MoodORM).options(selectinload(in_load_typing(MoodORM.tracks)))
    ).all()
    return [mood_from_orm(mood) for mood in moods]


def get_genres(session: Session) -> list[Genre]:
    genres = session.exec(
        select(GenreORM).options(selectinload(in_load_typing(GenreORM.tracks)))
    ).all()
    return [genre_from_orm(genre) for genre in genres]


def find_or_create_mood(session: Session, mood_name: str) -> MoodORM:
    normalized_name = mood_name.lower().strip()
    mood = session.exec(
        select(MoodORM).where(MoodORM.normalized_name == normalized_name)
    ).first()
    if mood:
        return mood
    new_mood = MoodORM(name=mood_name.strip(), normalized_name=normalized_name)
    session.add(new_mood)
    session.flush()
    return new_mood


def find_or_create_genre(session: Session, genre_name: str) -> GenreORM:
    normalized_name = genre_name.lower().strip()
    genre = session.exec(
        select(GenreORM).where(GenreORM.normalized_name == normalized_name)
    ).first()
    if genre:
        return genre
    new_genre = GenreORM(name=genre_name.strip(), normalized_name=normalized_name)
    session.add(new_genre)
    session.flush()
    return new_genre


def get_video_by_id(session: Session, id: int) -> MusicVideo | BaseError:
    orm_video = session.exec(
        select(MusicVideoORM).where(MusicVideoORM.id == id)
    ).first()
    return music_video_from_orm(orm_video) if orm_video else NotFoundError()


def search_tracks(session: Session, query: str, limit: int, offset: int) -> list[Track]:
    statement = (
        select(TrackORM)
        .where(col(TrackORM.title).ilike(f"%{query}%"))
        .limit(limit)
        .offset(offset)
        .options(
            selectinload(in_load_typing(TrackORM.files)),
            selectinload(in_load_typing(TrackORM.albums_links))
            .selectinload(in_load_typing(TrackAlbumLink.album))
            .selectinload(in_load_typing(AlbumORM.artists)),
        )
    )
    orm_tracks = session.exec(statement).all()
    return [track_from_orm(track) for track in orm_tracks]


# def delete_track(session: Session, id: int):
#   statement = select(TrackORM).where(TrackORM.id == id)
#   track = session.exec(statement).first()
#   session.delete(track)
