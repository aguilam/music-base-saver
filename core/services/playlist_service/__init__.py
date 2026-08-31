from core.errors import BaseError
from core.schemas import Playlist
from sqlmodel import Session
from core.services.playlist_service import playlist_repository


def get_playlist_by_id(session: Session, id: int) -> Playlist | BaseError:
    return playlist_repository.get_playlist_by_id(session, id)


def create_playlist(
    session: Session,
    user_id: int,
    title: str,
    tracks_id: list[int],
    is_public: bool = False,
    cover_path: int | None = None,
) -> Playlist | BaseError:
    return playlist_repository.create_playlist(
        session, user_id, title, is_public, tracks_id, cover_path
    )


def delete_playlist(session: Session, playlist_id: int) -> None:
    playlist_repository.delete_playlist(session, playlist_id)


def update_playlist(
    session: Session,
    playlist_id: int,
    user_id: int,
    title: str | None,
    track_ids: list[int] | None,
    owner_ids: list[int] | None,
    is_public: bool | None,
) -> Playlist | BaseError:
    return playlist_repository.update_playlist(
        session, playlist_id, user_id, title, track_ids, owner_ids, is_public
    )
