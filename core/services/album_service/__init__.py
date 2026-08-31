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
