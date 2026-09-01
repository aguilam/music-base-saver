from core.db.models import ArtistORM
from core.errors import BaseError
from core.schemas import ArtistShort, Artist, TrackShort
from sqlmodel import Session
from core.services.artist_service import artist_repository


def get_artist_by_id(session: Session, id: int) -> Artist | BaseError:
    return artist_repository.get_artist_by_id(session, id)


def find_or_create_artist(session: Session, name: str) -> ArtistORM:
    return artist_repository.find_or_create_artist(session, name)


def get_all_artists(
    session: Session, size: int | None = None, offset: int | None = None
) -> list[ArtistShort]:
    return artist_repository.get_all_artists(session, size, offset)


def get_artist_top_songs(session: Session, name: str, count: int) -> list[TrackShort]:
    return artist_repository.get_tracks_by_artist_name(session, name, count)


def get_artists_cursor(
    session: Session, cursor: str | None, limit: int = 20
) -> tuple[list[ArtistShort], str | None]:
    return artist_repository.get_artists_cursor(session, limit, cursor)


def get_artist_by_name(session: Session, name: str) -> Artist | BaseError:
    return artist_repository.get_artist_by_name(session, name)


def get_artists_random_tracks(
    session: Session, artists: list[str], count: int
) -> list[TrackShort]:
    return artist_repository.get_artists_random_tracks(session, artists, count)


def get_artist_orm_by_id(session: Session, artist_id: int) -> ArtistORM | None:
    return artist_repository.get_artist_orm_by_id(session, artist_id)


def get_artist_orm_by_name(session: Session, name: str) -> ArtistORM | None:
    return artist_repository.get_artist_orm_by_name(session, name)


def get_artists_by_name(
    session: Session, name: list[str], count: int
) -> list[ArtistShort] | BaseError:
    return artist_repository.get_artists_by_name(session, name, count)
