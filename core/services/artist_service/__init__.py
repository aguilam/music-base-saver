from core.errors import BaseError
from core.schemas import ArtistShort, Artist, TrackShort
from sqlmodel import Session
from core.services.artist_service import artist_repository


def get_artist_by_id(session: Session, id: int) -> Artist | BaseError:
    return artist_repository.get_artist_by_id(session, id)


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
