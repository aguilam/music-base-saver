from core.errors import NotFoundError, BaseError
from core.utils import encode_datetime_cursor, decode_datetime_cursor
from core.db.mappers import album_from_orm, album_short_from_orm
from core.schemas import Album, AlbumShort
from core.db.utils import in_load_typing
from core.db.models import AlbumORM, ArtistORM, TrackAlbumLink, TrackORM
from sqlalchemy import or_, and_
from sqlalchemy.orm import selectinload
from sqlmodel import select, col, Session


def find_or_create_album(
    session: Session,
    title: str,
    artists_names: list[str] | None = None,
    year: int | None = None,
    description: str | None = None,
    type: str | None = None,
) -> AlbumORM:
    normalized_title = title.lower().strip()
    stmt = select(AlbumORM).where(AlbumORM.normalized_title == normalized_title)
    if artists_names:
        stmt = (
            stmt.join(col(AlbumORM.artists))
            .where(col(ArtistORM.name).in_(artists_names))
            .distinct()
        )
    existed_album = session.exec(stmt).first()
    if existed_album:
        return existed_album
    new_album = AlbumORM(
        title=title,
        normalized_title=normalized_title,
        year=year,
        description=description,
        type=type,
    )
    session.add(new_album)
    session.flush()
    return new_album


def get_all_albums(session: Session, size: int, offset: int) -> list[AlbumShort]:
    statement = (
        select(AlbumORM)
        .options(
            selectinload(in_load_typing(AlbumORM.tracks_links))
            .selectinload(in_load_typing(TrackAlbumLink.track))
            .selectinload(in_load_typing(TrackORM.files)),
            selectinload(in_load_typing(AlbumORM.tracks_links))
            .selectinload(in_load_typing(TrackAlbumLink.track))
            .selectinload(in_load_typing(TrackORM.albums_links)),
            selectinload(in_load_typing(AlbumORM.artists)),
        )
        .limit(size)
        .offset(offset)
    )
    orm_albums = session.exec(statement).all()
    return [album_short_from_orm(album) for album in orm_albums]


def get_albums_cursor(
    session: Session, limit: int, cursor: str | None
) -> tuple[list[AlbumShort], str | None]:
    last_id, created_at = decode_datetime_cursor(cursor) if cursor else (None, None)
    statement = (
        select(AlbumORM)
        .order_by(col(AlbumORM.created_at).desc(), col(AlbumORM.id).desc())
        .limit(limit + 1)
    )
    if last_id is not None and created_at is not None:
        statement = statement.where(
            or_(
                col(AlbumORM.created_at) < created_at,
                and_(
                    col(AlbumORM.created_at) == created_at,
                    col(AlbumORM.id) < last_id,
                ),
            )
        )
    albums = list(session.exec(statement).all())
    next_cursor = None
    if len(albums) > limit:
        albums.pop()
        last_item = albums[-1]
        next_cursor = encode_datetime_cursor(last_item.id, last_item.created_at)
    return [album_short_from_orm(album) for album in albums], next_cursor


def get_album_by_id(session: Session, id: int) -> Album | BaseError:
    statement = (
        select(AlbumORM)
        .where(AlbumORM.id == id)
        .options(
            selectinload(in_load_typing(AlbumORM.tracks_links))
            .selectinload(in_load_typing(TrackAlbumLink.track))
            .selectinload(in_load_typing(TrackORM.files)),
            selectinload(in_load_typing(AlbumORM.tracks_links))
            .selectinload(in_load_typing(TrackAlbumLink.track))
            .selectinload(in_load_typing(TrackORM.albums_links)),
            selectinload(in_load_typing(AlbumORM.artists)),
        )
    )
    orm_album = session.exec(statement).first()
    return album_from_orm(orm_album) if orm_album else NotFoundError()


def get_album_orm_by_id(session: Session, id: int) -> AlbumORM | None:
    return session.get(AlbumORM, id)


def get_album_by_title(session: Session, title: str) -> Album | BaseError:
    album = session.exec(select(AlbumORM).where(col(AlbumORM.title) == title)).first()
    return album_from_orm(album) if album else NotFoundError()


def search_albums(
    session: Session, query: str, limit: int, offset: int
) -> list[AlbumShort]:
    statement = (
        select(AlbumORM)
        .where(col(AlbumORM.title).ilike(f"%{query}%"))
        .limit(limit)
        .offset(offset)
        .options(
            selectinload(in_load_typing(AlbumORM.tracks_links))
            .selectinload(in_load_typing(TrackAlbumLink.track))
            .selectinload(in_load_typing(TrackORM.files)),
            selectinload(in_load_typing(AlbumORM.tracks_links))
            .selectinload(in_load_typing(TrackAlbumLink.track))
            .selectinload(in_load_typing(TrackORM.albums_links)),
            selectinload(in_load_typing(AlbumORM.artists)),
        )
    )
    orm_albums = session.exec(statement).all()
    return [album_short_from_orm(album) for album in orm_albums]


def get_album_orm_by_title(session: Session, title: str) -> AlbumORM | None:
    return session.exec(select(AlbumORM).where(AlbumORM.title == title)).first()
