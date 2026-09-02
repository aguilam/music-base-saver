from core.schemas import Playlist
from core.db.mappers import playlist_from_orm
from core.errors import NotFoundError, BaseError, ForbiddenError
from core.db.utils import in_load_typing
from core.db.models import (
    AlbumORM,
    TrackAlbumLink,
    TrackORM,
    PlaylistORM,
    PlaylistTrackLink,
    UserORM,
)
from sqlalchemy.orm import selectinload
from sqlmodel import select, col, Session, delete


def get_playlist_by_id(session: Session, id: int) -> Playlist | BaseError:
    statement = (
        select(PlaylistORM)
        .where(PlaylistORM.id == id)
        .options(
            selectinload(in_load_typing(PlaylistORM.owners)),
            selectinload(in_load_typing(PlaylistORM.track_links))
            .selectinload(in_load_typing(PlaylistTrackLink.track))
            .selectinload(in_load_typing(TrackORM.files)),
            selectinload(in_load_typing(PlaylistORM.track_links))
            .selectinload(in_load_typing(PlaylistTrackLink.track))
            .selectinload(in_load_typing(TrackORM.albums_links))
            .selectinload(in_load_typing(TrackAlbumLink.album))
            .selectinload(in_load_typing(AlbumORM.artists)),
        )
    )
    orm_playlist = session.exec(statement).first()
    return playlist_from_orm(orm_playlist) if orm_playlist else NotFoundError()


def update_playlist(
    session: Session,
    playlist_id: int,
    user_id: int,
    title: str | None,
    track_ids: list[int] | None,
    owner_ids: list[int] | None,
    is_public: bool | None,
) -> Playlist | BaseError:
    playlist = session.exec(
        select(PlaylistORM).where(PlaylistORM.id == playlist_id)
    ).first()
    if playlist is None:
        return NotFoundError()
    if user_id not in [owner.id for owner in playlist.owners]:
        return ForbiddenError()
    if title is not None:
        playlist.title = title
    if is_public is not None:
        playlist.is_public = is_public
    if owner_ids is not None:
        playlist.owners = session.exec(
            select(UserORM).where(col(UserORM.id).in_(owner_ids))
        ).all()
    if track_ids is not None:
        session.exec(
            delete(PlaylistTrackLink).where(
                col(PlaylistTrackLink.playlist_id) == playlist.id
            )
        )
        session.flush()
        session.add_all(
            PlaylistTrackLink(
                playlist_id=playlist.id,
                track_id=track_id,
                position=position,
            )
            for position, track_id in enumerate(track_ids, 1)
        )
    session.flush()
    return playlist_from_orm(playlist)


def delete_playlist(session: Session, id: int):
    statement = delete(PlaylistORM).where(col(PlaylistORM.id) == id)
    session.exec(statement)


def create_playlist(
    session: Session,
    user_id: int,
    title: str,
    is_public: bool,
    tracks_id: list[int],
    cover_path: int | None = None,
) -> Playlist | BaseError:
    user = session.exec(select(UserORM).where(UserORM.id == user_id)).first()
    if user is None:
        return NotFoundError()
    playlist = PlaylistORM(
        title=title, cover_path=cover_path, is_public=is_public, owners=[user]
    )
    session.add(playlist)
    session.flush()
    for position, track_id in enumerate(tracks_id, start=1):
        trackLink = PlaylistTrackLink(
            playlist_id=playlist.id, track_id=track_id, position=position
        )
        session.add(trackLink)
    session.flush()
    return playlist_from_orm(playlist)


def search_playlists(
    session: Session, query: str, limit: int, offset: int
) -> list[Playlist]:
    orm_playlists = session.exec(
        select(PlaylistORM)
        .where(col(PlaylistORM.title).ilike(f"%{query}%"))
        .limit(limit)
        .offset(offset)
    ).all()
    return [playlist_from_orm(playlist) for playlist in orm_playlists]


def get_playlist_orm_by_id(session: Session, id: int) -> PlaylistORM | None:
    return session.get(PlaylistORM, id)
