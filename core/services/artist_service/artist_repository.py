from core.errors import NotFoundError, BaseError
from core.db.utils import in_load_typing
from core.db.mappers import artist_short_from_orm, track_short_from_orm, artist_from_orm
from core.utils import decode_datetime_cursor, encode_datetime_cursor
from core.schemas import ArtistShort, TrackShort, Artist
from sqlalchemy import or_, and_, func
from sqlalchemy.orm import selectinload
from sqlmodel import select, col, Session
from core.db.models import TrackORM, ArtistORM, ArtistAlias, AlbumORM


def get_tracks_by_artist_name(
    session: Session, artist_name: str, count: int
) -> list[TrackShort]:
    tracks = session.exec(
        select(TrackORM)
        .join(col(TrackORM.artists))
        .where(ArtistORM.name == artist_name)
        .limit(count)
    ).all()
    return [track_short_from_orm(track) for track in tracks]


def find_or_create_artist(session: Session, name: str) -> ArtistORM:
    normalized_name = name.lower().strip()
    existed_artist = session.exec(
        select(ArtistORM).where(
            or_(
                col(ArtistORM.normalized_name) == normalized_name,
                col(ArtistORM.aliases).any(
                    col(ArtistAlias.normalized_name) == normalized_name
                ),
            )
        )
    ).first()
    if existed_artist:
        return existed_artist
    new_artist = ArtistORM(name=name, normalized_name=normalized_name)
    session.add(new_artist)
    session.flush()
    return new_artist


def get_all_artists(
    session: Session, size: int | None, offset: int | None
) -> list[ArtistShort]:
    statement = select(ArtistORM).options(
        selectinload(in_load_typing(ArtistORM.albums))
    )
    if size:
        statement = statement.limit(size)
    if offset:
        statement = statement.offset(offset)
    orm_artists = session.exec(statement).all()
    return [artist_short_from_orm(artist) for artist in orm_artists]


def get_artists_cursor(
    session: Session, limit: int, cursor: str | None
) -> tuple[list[ArtistShort], str | None]:
    last_id, created_at = decode_datetime_cursor(cursor) if cursor else (None, None)
    statement = (
        select(ArtistORM)
        .order_by(col(ArtistORM.created_at).desc(), col(ArtistORM.id).desc())
        .limit(limit + 1)
    )
    if last_id is not None and created_at is not None:
        statement = statement.where(
            or_(
                col(ArtistORM.created_at) < created_at,
                and_(
                    col(ArtistORM.created_at) == created_at,
                    col(ArtistORM.id) < last_id,
                ),
            )
        )
    artists = list(session.exec(statement).all())
    next_cursor = None
    if len(artists) > limit:
        artists.pop()
        last_item = artists[-1]
        next_cursor = encode_datetime_cursor(last_item.id, last_item.created_at)
    return [artist_short_from_orm(artist) for artist in artists], next_cursor


def get_artist_by_id(session: Session, id: int) -> Artist | BaseError:
    statement = (
        select(ArtistORM)
        .where(ArtistORM.id == id)
        .options(
            selectinload(in_load_typing(ArtistORM.albums)).selectinload(
                in_load_typing(AlbumORM.tracks_links)
            ),
            selectinload(in_load_typing(ArtistORM.albums)).selectinload(
                in_load_typing(AlbumORM.artists)
            ),
        )
    )
    orm_artist = session.exec(statement).first()
    return artist_from_orm(orm_artist) if orm_artist else NotFoundError()


def get_artists_random_tracks(
    session: Session, artists: list[str], count: int
) -> list[TrackShort]:
    normalized_names = [name.strip().lower() for name in artists]
    stmt = (
        select(TrackORM)
        .join(col(TrackORM.artists))
        .where(col(ArtistORM.normalized_name).in_(normalized_names))
        .order_by(func.random())
        .limit(count)
    )
    tracks = session.exec(stmt).all()
    return [track_short_from_orm(track) for track in tracks]


def get_artists_by_name(
    session: Session, artists: list[str], count: int
) -> list[ArtistShort]:
    normalized_names = [artist.strip().lower() for artist in artists]
    db_artists = session.exec(
        select(ArtistORM)
        .where(col(ArtistORM.normalized_name).in_(normalized_names))
        .limit(count)
    ).all()
    return [artist_short_from_orm(artist) for artist in db_artists]


def get_artist_orm_by_name(session: Session, name: str) -> ArtistORM | None:
    return session.exec(select(ArtistORM).where(ArtistORM.name == name)).first()


def get_artist_orm_by_id(session: Session, id: int) -> ArtistORM | None:
    return session.get(ArtistORM, id)


def get_artist_by_name(session: Session, name: str) -> Artist | BaseError:
    orm_artist = session.exec(
        select(ArtistORM)
        .outerjoin(ArtistAlias)
        .where((col(ArtistORM.name).ilike(name)) | (col(ArtistAlias.name).ilike(name)))
    ).first()
    return artist_from_orm(orm_artist) if orm_artist else NotFoundError()


def search_artists(
    session: Session, query: str, limit: int, offset: int
) -> list[ArtistShort]:
    statement = (
        select(ArtistORM)
        .outerjoin(ArtistAlias)
        .where(
            (col(ArtistORM.name).ilike(f"%{query}%"))
            | (col(ArtistAlias.name).ilike(f"%{query}%"))
        )
        .limit(limit)
        .offset(offset)
        .options(selectinload(in_load_typing(ArtistORM.albums)))
    )
    orm_artists = session.exec(statement).all()
    return [artist_short_from_orm(artist) for artist in orm_artists]
