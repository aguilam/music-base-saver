from core.db.models import AlbumORM
from core.errors import BaseError
from core.schemas import Album, AlbumShort
from sqlmodel import Session
from core.services.album_service import album_repository


def get_album_by_id(session: Session, id: int) -> Album | BaseError:
    return album_repository.get_album_by_id(session, id)


def get_all_albums(
    session: Session, size: int = 10, offset: int = 0
) -> list[AlbumShort]:
    return album_repository.get_all_albums(session, size, offset)


def get_albums_cursor(
    session: Session, cursor: str | None, limit: int = 20
) -> tuple[list[AlbumShort], str | None]:
    return album_repository.get_albums_cursor(session, limit, cursor)


def find_or_create_album(
    session: Session,
    title: str,
    artists_names: list[str] | None = None,
    year: int | None = None,
    description: str | None = None,
    type: str | None = None,
) -> AlbumORM:
    return album_repository.find_or_create_album(
        session, title, artists_names, year, description, type
    )


def get_album_orm_by_title(session: Session, title: str) -> AlbumORM | None:
    return album_repository.get_album_orm_by_title(session, title)


def get_album_orm_by_id(session: Session, id: int) -> AlbumORM | None:
    return album_repository.get_album_orm_by_id(session, id)


def get_album_by_title(session: Session, title: str) -> Album | BaseError:
    return album_repository.get_album_by_title(session, title)
