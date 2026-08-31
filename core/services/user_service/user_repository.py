from core.db.mappers import (
    track_short_from_orm,
    listed_user_from_orm,
    api_key_from_orm,
    stored_user_from_orm,
    album_short_from_orm,
    artist_short_from_orm,
    playlist_from_orm,
    provider_key_from_orm,
)
from core.schemas import (
    TrackShort,
    ApiKey,
    StoredUser,
    AlbumShort,
    ArtistShort,
    Playlist,
    ProviderKey,
)
from core.errors import NotFoundError, BaseError, ForbiddenError
from core.db.utils import in_load_typing
from sqlalchemy.orm import selectinload
from sqlmodel import select, col, Session, update, delete
from core.db.models import (
    UserORM,
    StoredUserORM,
    ApiKeyORM,
    PlaylistORM,
    ProviderKeyORM,
)


def get_all_users(session: Session) -> list[StoredUser]:
    statement = select(UserORM)
    users = session.exec(statement)
    return [stored_user_from_orm(StoredUserORM.model_validate(user)) for user in users]


def get_user_api_keys(session: Session, user_id: int):
    statement = select(ApiKeyORM).where(ApiKeyORM.user_id == user_id)
    keys = session.exec(statement).all()
    return [api_key_from_orm(key) for key in keys]


def check_api_key_availability(session: Session, api_key: str) -> ApiKey | BaseError:
    key = session.exec(
        select(ApiKeyORM).where(ApiKeyORM.key == api_key, ~col(ApiKeyORM.revoked))
    ).first()
    return api_key_from_orm(key) if key else NotFoundError()


def create_api_key(session: Session, user_id: int, key: str) -> ApiKey:
    api_key = ApiKeyORM(user_id=user_id, key=key)
    session.add(api_key)
    session.flush()
    return api_key_from_orm(api_key)


def revoke_api_key(session: Session, id: int):
    session.exec(update(ApiKeyORM).where(col(ApiKeyORM.id) == id).values(revoked=True))
    session.flush()


def get_user_by_name(session: Session, username: str) -> StoredUser | BaseError:
    orm_user = session.exec(select(UserORM).where(UserORM.username == username)).first()
    return (
        stored_user_from_orm(StoredUserORM.model_validate(orm_user))
        if orm_user
        else NotFoundError()
    )


def get_user_by_id(session: Session, id: int) -> StoredUser | None:
    orm_user = session.exec(select(UserORM).where(UserORM.id == id)).first()
    return (
        stored_user_from_orm(StoredUserORM.model_validate(orm_user))
        if orm_user
        else None
    )


def create_user(
    session: Session, username: str, email: str, password: str
) -> StoredUser:
    new_user = UserORM(username=username, email=email, password=password)
    session.add(new_user)
    session.flush()
    return stored_user_from_orm(StoredUserORM.model_validate(new_user))


def update_user(
    session: Session,
    changed_user: UserORM | None,
    acting_user_id: int,
    set_is_admin: bool | None,
    new_password: str | None,
    new_username: str | None,
) -> StoredUser | BaseError:
    if changed_user is None:
        return NotFoundError()
    if set_is_admin is None and not new_password and not new_username:
        return ForbiddenError()
    same_user = changed_user.id == acting_user_id
    is_can_change_admin = changed_user.is_admin
    if not same_user:
        acting_user = session.exec(
            select(UserORM).where(UserORM.id == acting_user_id)
        ).first()
        if acting_user is None:
            return NotFoundError()
        is_can_change_admin = acting_user.is_admin
    can_change = same_user or is_can_change_admin
    if not can_change:
        return ForbiddenError()
    if set_is_admin is not None:
        if not is_can_change_admin:
            return ForbiddenError()
        changed_user.is_admin = set_is_admin
    if new_password and can_change:
        changed_user.password = new_password
    if new_username and can_change:
        changed_user.username = new_username
    return stored_user_from_orm(StoredUserORM.model_validate(changed_user))


def update_user_by_username(
    session: Session,
    acting_user_id: int,
    current_username: str,
    new_username: str | None,
    new_password: str | None,
    set_is_admin: bool | None,
) -> StoredUser | BaseError:
    changed_user = session.exec(
        select(UserORM).where(UserORM.username == current_username)
    ).first()
    return update_user(
        session=session,
        changed_user=changed_user,
        acting_user_id=acting_user_id,
        new_password=new_password,
        set_is_admin=set_is_admin,
        new_username=new_username,
    )


def update_user_by_id(
    session: Session,
    acting_user_id: int,
    changed_user_id: int,
    new_username: str | None,
    new_password: str | None,
    set_is_admin: bool | None,
) -> StoredUser | BaseError:
    changed_user = session.exec(
        select(UserORM).where(UserORM.id == changed_user_id)
    ).first()
    return update_user(
        session=session,
        changed_user=changed_user,
        acting_user_id=acting_user_id,
        new_password=new_password,
        set_is_admin=set_is_admin,
        new_username=new_username,
    )


def get_user_by_apikey(session: Session, api_key: str) -> StoredUser | None:
    orm_user = session.exec(
        select(UserORM).join(col(UserORM.api_keys)).where(ApiKeyORM.key == api_key)
    ).first()
    return (
        stored_user_from_orm(StoredUserORM.model_validate(orm_user))
        if orm_user
        else None
    )


def delete_user_by_id(session: Session, user_id: int) -> int:
    stm = delete(UserORM).where(col(UserORM.id) == user_id)
    result = session.exec(stm)
    session.commit()
    return result.rowcount


def delete_user_by_username(session: Session, username: str) -> int:
    stm = delete(UserORM).where(col(UserORM.username) == username)
    result = session.exec(stm)
    session.commit()
    return result.rowcount


def get_all_user_starred(
    session: Session, user_id: int
) -> tuple[list[TrackShort], list[AlbumShort], list[ArtistShort]] | None:
    user = session.exec(select(UserORM).where(UserORM.id == user_id)).first()
    if user is None:
        return None
    starred_tracks = [track_short_from_orm(track) for track in user.starred_tracks]
    starred_albums = [album_short_from_orm(album) for album in user.starred_albums]
    starred_artists = [artist_short_from_orm(artist) for artist in user.starred_artists]

    return (starred_tracks, starred_albums, starred_artists)


def get_user_playlists(
    session: Session, user_id: int, size: int, offset: int
) -> list[Playlist]:
    statement = (
        (
            select(PlaylistORM)
            .join(col(PlaylistORM.owners))
            .where(UserORM.id == user_id)
            .distinct()
            .options(
                selectinload(in_load_typing(PlaylistORM.owners)),
                selectinload(in_load_typing(PlaylistORM.track_links)),
            )
        )
        .limit(size)
        .offset(offset)
    )
    orm_playlists = session.exec(statement).all()
    return [playlist_from_orm(playlist) for playlist in orm_playlists]


def get_provider_key(
    session: Session, provider: str, user_id: int
) -> ProviderKey | None:
    statement = select(ProviderKeyORM).where(
        ProviderKeyORM.provider == provider, ProviderKeyORM.user_id == user_id
    )
    key = session.exec(statement).first()
    return provider_key_from_orm(key) if key else None


def change_provider_key(session: Session, id: int, new_value: str):
    session.exec(
        update(ProviderKeyORM).where(col(ProviderKeyORM.id) == id).values(key=new_value)
    )
    session.flush()


def create_provider_key(
    session: Session, user_id: int, key: str, provider: str
) -> ProviderKey:
    provider_key = ProviderKeyORM(user_id=user_id, key=key, provider=provider)
    session.add(provider_key)
    session.flush()
    return provider_key_from_orm(provider_key)


def delete_provider_key(session: Session, id: int):
    session.exec(delete(ProviderKeyORM).where(col(ProviderKeyORM.id) == id))
    session.flush()


def get_user_provider_keys(session: Session, user_id: int) -> list[ProviderKey]:
    statement = select(ProviderKeyORM).where(ProviderKeyORM.user_id == user_id)
    keys = session.exec(statement).all()
    return [provider_key_from_orm(key) for key in keys]
