from core.db.models import StarredArtist, StarredAlbum, StarredTrack
import secrets
from core.schemas import (
    ProviderKey,
    ApiKey,
    TrackShort,
    AlbumShort,
    ArtistShort,
    Playlist,
    StoredUser,
)
from core.errors import BaseError, NotFoundError, ForbiddenError
from sqlmodel import Session, select, col
from core.services.user_service import user_repository

STAR_LINK_MAP = {
    "track": lambda user_id, obj_id: StarredTrack(user_id=user_id, track_id=obj_id),
    "album": lambda user_id, obj_id: StarredAlbum(user_id=user_id, album_id=obj_id),
    "artist": lambda user_id, obj_id: StarredArtist(user_id=user_id, artist_id=obj_id),
}

UNSTAR_LINK_MAP = {
    "track": (StarredTrack, "song_id"),
    "album": (StarredAlbum, "album_id"),
    "artist": (StarredArtist, "artist_id"),
}


def delete_user_by_username(
    session: Session, username: str, user_id: int
) -> int | BaseError:
    user = user_repository.get_user_by_id(session, user_id)
    if user is None:
        return NotFoundError()
    if user.is_admin or user.username == username:
        return user_repository.delete_user_by_username(session, username)
    return ForbiddenError()


def delete_user_by_id(session: Session, id: int, user_id: int) -> int | BaseError:
    user = user_repository.get_user_by_id(session, user_id)
    if user is None:
        return NotFoundError()
    if user.is_admin or user.id == id:
        return user_repository.delete_user_by_id(session, id)
    return ForbiddenError()


def update_user_by_username(
    session: Session,
    acting_user_id: int,
    current_username: str,
    new_username: str | None = None,
    new_password: str | None = None,
    set_is_admin: bool | None = None,
) -> StoredUser | BaseError:
    return user_repository.update_user_by_username(
        session=session,
        current_username=current_username,
        acting_user_id=acting_user_id,
        new_password=new_password,
        set_is_admin=set_is_admin,
        new_username=new_username,
    )


def update_user_by_id(
    session: Session,
    acting_user_id: int,
    changed_user_id: int,
    new_username: str | None = None,
    new_password: str | None = None,
    set_is_admin: bool | None = None,
) -> StoredUser | BaseError:
    return user_repository.update_user_by_id(
        session=session,
        changed_user_id=changed_user_id,
        acting_user_id=acting_user_id,
        new_password=new_password,
        set_is_admin=set_is_admin,
        new_username=new_username,
    )


def create_user(
    session: Session, username: str, email: str, password: str
) -> StoredUser:
    return user_repository.create_user(session, username, email, password)


def get_user(
    session: Session, username: str | None = None, user_id: int | None = None
) -> StoredUser | None | BaseError:
    if username is not None:
        user = user_repository.get_user_by_name(session, username)
        if isinstance(user, BaseError):
            return user
        return user
    elif user_id is not None:
        user = user_repository.get_user_by_id(session, user_id)
        return user
    else:
        return None


def get_all_users(session: Session) -> list[StoredUser]:
    users = user_repository.get_all_users(session)
    return users


def get_all_user_starred(
    session: Session, user_id: int
) -> tuple[list[TrackShort], list[AlbumShort], list[ArtistShort]] | None:
    return user_repository.get_all_user_starred(session, user_id)


def get_user_api_keys(session: Session, user_id: int) -> list[ApiKey]:
    return user_repository.get_user_api_keys(session, user_id)


def revoke_api_key(session: Session, key_id: int):
    user_repository.revoke_api_key(session, key_id)


def create_api_key(session: Session, user_id: int) -> ApiKey | BaseError:
    user = user_repository.get_user_by_id(session, user_id)
    if user is None:
        return NotFoundError()
    key = secrets.token_hex(16)
    return user_repository.create_api_key(session, user_id, key=f"ms_{key}")


def check_api_key_availability(session: Session, api_key: str) -> ApiKey | BaseError:
    key = user_repository.check_api_key_availability(session, api_key)
    return key


def star(
    session: Session, user_id: int, object_id: int, object_type: str
) -> BaseError | None:
    stap_tuple = STAR_LINK_MAP.get(object_type)
    if stap_tuple is None:
        return NotFoundError()
    link = stap_tuple(user_id, object_id)
    session.add(link)


def unstar(
    session: Session, user_id: int, object_id: int, object_type: str
) -> BaseError | None:
    unstar_tuple = UNSTAR_LINK_MAP.get(object_type, None)
    if unstar_tuple is None:
        return NotFoundError()
    model, id_field = unstar_tuple
    statement = select(model).where(
        col(model.user_id) == user_id,
        getattr(model, id_field) == object_id,
    )
    link = session.exec(statement).first()
    if link is None:
        return NotFoundError()
    session.delete(link)


def get_user_playlists(
    session: Session, user_id: int, size: int = 10, offset: int = 0
) -> list[Playlist]:
    return user_repository.get_user_playlists(session, user_id, size, offset)


def delete_provider_key(session: Session, key_id: int) -> None:
    user_repository.delete_provider_key(session, key_id)


def create_provider_key(
    session: Session, user_id: int, key: str, provider: str
) -> ProviderKey | BaseError:
    user = user_repository.get_user_by_id(session, user_id)
    if user is None:
        return NotFoundError()
    return user_repository.create_provider_key(
        session, user_id, key=key, provider=provider
    )


def change_provider_key(
    session: Session, user_id: int, key_id: int, new_key: str
) -> BaseError | None:
    user = user_repository.get_user_by_id(session, user_id)
    if user is None:
        return NotFoundError()
    user_repository.change_provider_key(session, key_id, new_value=new_key)


def get_user_provider_keys(session: Session, user_id: int) -> list[ProviderKey]:
    return user_repository.get_user_provider_keys(session, user_id)
