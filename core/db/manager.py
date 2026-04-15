from sqlmodel import (
    SQLModel,
    create_engine,
    Session,
    select,
    literal,
    delete,
    col,
)

from sqlalchemy import tuple_, func
from core.db.mappers import (
    artist_from_orm,
    album_from_orm,
    playlist_from_orm,
    track_from_orm,
    music_video_from_orm,
    user_from_orm,
)
from core.db.models import (
    UserORM,
    ArtistAlias,
    ArtistORM,
    AlbumORM,
    Genre,
    Mood,
    TrackLink,
    TrackORM,
    PlaylistORM,
    MusicVideoORM,
)


def admin_create(engine):
    with Session(engine) as session:
        statement = select(func.count()).select_from(UserORM)
        users_count = session.exec(statement).one()
        if users_count < 1:
            admin = UserORM(
                username="admin",
                password="admin",
                email="admin@mail.com",
                is_admin=True,
            )
            session.add(admin)
            session.commit()


from sqlalchemy.orm import selectinload


class DBManager:
    def __init__(self) -> None:
        self.engine = create_engine("sqlite:///database.db")
        SQLModel.metadata.create_all(self.engine)
        admin_create(self.engine)

    def get_session(self) -> Session:
        return Session(self.engine)

    def get_artist_by_name(self, session: Session, name: str):
        orm_artist = session.exec(
            select(ArtistORM)
            .outerjoin(ArtistAlias)
            .where(
                (col(ArtistORM.name).ilike(name)) | (col(ArtistAlias.name).ilike(name))
            )
        ).first()
        return artist_from_orm(orm_artist) if orm_artist else None

    def get_album_by_name(self, session: Session, title: str):
        return session.exec(select(AlbumORM).where(AlbumORM.title == title)).first()

    def get_moods(self, session: Session) -> list[Mood] | None:
        moods = (
            session.execute(select(Mood).options(selectinload(Mood.tracks)))
            .scalars()
            .all()
        )
        return moods

    def get_genres(self, session: Session) -> list[Genre] | None:
        genres = (
            session.execute(select(Genre).options(selectinload(Genre.tracks)))
            .scalars()
            .all()
        )
        return genres

    def get_track_by_name(self, session: Session, title: str):
        orm_track = session.exec(
            select(TrackORM).where(col(TrackORM.title).ilike(title))
        ).first()
        return track_from_orm(orm_track) if orm_track else None

    def get_user_by_name(self, session: Session, username: str):
        orm_user = session.exec(
            select(UserORM).where(UserORM.username == username)
        ).first()
        return user_from_orm(orm_user) if orm_user else None

    def get_user_by_id(self, session: Session, id: int):
        orm_user = session.exec(select(UserORM).where(UserORM.id == id)).first()
        return user_from_orm(orm_user) if orm_user else None

    def get_video_by_id(self, session: Session, id: int):
        orm_video = session.exec(
            select(MusicVideoORM).where(MusicVideoORM.id == id)
        ).first()
        return music_video_from_orm(orm_video) if orm_video else None

    def get_playlist_by_id(self, session: Session, id: int):
        statement = (
            select(PlaylistORM)
            .where(PlaylistORM.id == id)
            .options(
                selectinload(PlaylistORM.owner),
                selectinload(PlaylistORM.tracks).selectinload(TrackORM.links),
                selectinload(PlaylistORM.tracks)
                .selectinload(TrackORM.album)
                .selectinload(AlbumORM.artist_rel),
            )
        )
        orm_playlist = session.exec(statement).first()
        return playlist_from_orm(orm_playlist) if orm_playlist else None

    def get_user_by_apikey(self, session: Session, api_key: str) -> UserORM | None:
        return session.exec(select(UserORM).where(UserORM.api_key == api_key)).first()

    def search_artists(self, session: Session, query: str, limit: int, offset: int):
        statement = (
            select(ArtistORM)
            .outerjoin(ArtistAlias)
            .where(
                (col(ArtistORM.name).ilike(f"%{query}%"))
                | (col(ArtistAlias.name).ilike(f"%{query}%"))
            )
            .limit(limit)
            .offset(offset)
            .options(selectinload(ArtistORM.albums))
        )
        orm_artists = session.exec(statement).all()
        return [artist_from_orm(artist) for artist in orm_artists]

    def search_albums(self, session: Session, query: str, limit: int, offset: int):
        statement = (
            select(AlbumORM)
            .where(col(AlbumORM.title).ilike(f"%{query}%"))
            .limit(limit)
            .offset(offset)
            .options(
                selectinload(AlbumORM.tracks).selectinload(TrackORM.links),
                selectinload(AlbumORM.tracks).selectinload(TrackORM.album),
                selectinload(AlbumORM.artist_rel),
            )
        )
        orm_albums = session.exec(statement).all()
        return [album_from_orm(album) for album in orm_albums]

    def search_tracks(self, session: Session, query: str, limit: int, offset: int):
        statement = (
            select(TrackORM)
            .where(col(TrackORM.title).ilike(f"%{query}%"))
            .limit(limit)
            .offset(offset)
            .options(
                selectinload(TrackORM.links),
                selectinload(TrackORM.album).selectinload(AlbumORM.artist_rel),
            )
        )
        orm_tracks = session.exec(statement).all()
        return [track_from_orm(track) for track in orm_tracks]

    def search_playlists(self, session: Session, query: str, limit: int, offset: int):
        orm_playlists = session.exec(
            select(PlaylistORM)
            .where(col(PlaylistORM.name).ilike(f"%{query}%"))
            .limit(limit)
            .offset(offset)
        ).all()
        return [playlist_from_orm(playlist) for playlist in orm_playlists]

    def get_all_user_starred(self, session: Session, user_id: int):
        user = self.get_user_by_id(session, user_id)
        starred_tracks = [track_from_orm(track) for track in user.starred_tracks]
        starred_albums = [album_from_orm(album) for album in user.starred_albums]
        starred_artists = [artist_from_orm(artist) for artist in user.starred_artists]

        return (starred_tracks, starred_albums, starred_artists)

    def get_user_playlists(self, session: Session, user_id: int):
        statement = (
            select(PlaylistORM)
            .where(PlaylistORM.owner_id == user_id)
            .options(selectinload(PlaylistORM.owner), selectinload(PlaylistORM.tracks))
        )
        orm_playlists = session.exec(statement).all()
        return [playlist_from_orm(playlist) for playlist in orm_playlists]

    def add(self, session: Session, obj):
        session.add(obj)
        session.flush()
        return obj

    def delete_track(self, session: Session, id: int):
        statement = select(TrackORM).where(TrackORM.id == id)
        track = session.exec(statement).first()
        session.delete(track)

    def bulk_delete_by_links(
        self, session: Session, provider_link: list[tuple[str, str]]
    ):
        select_ids = select(TrackLink.id, TrackLink.track_id).where(
            tuple_(TrackLink.link_provider, TrackLink.link).in_(provider_link)
        )
        ids_statement = session.exec(select_ids).all()
        links_ids = [r[0] for r in ids_statement]
        track_ids = [r[1] for r in ids_statement]
        delete_links_statement = delete(TrackLink).where(TrackLink.id.in_(links_ids))
        session.exec(delete_links_statement)
        delete_tracks_statement = delete(TrackORM).where(TrackORM.id.in_(track_ids))
        tracks = session.exec(delete_tracks_statement)
        session.commit()
        return tracks.rowcount

    def get_all_tracks(self, session: Session):
        statement = select(TrackORM).options(selectinload(TrackORM.links))
        orm_tracks = session.exec(statement).all()
        return [track_from_orm(track) for track in orm_tracks]

    def get_all_artists(self, session: Session):
        statement = select(ArtistORM).options(selectinload(ArtistORM.albums))
        orm_artists = session.exec(statement).all()
        return [artist_from_orm(artist) for artist in orm_artists]

    def get_all_albums(self, session: Session):
        statement = select(AlbumORM).options(
            selectinload(AlbumORM.tracks).selectinload(TrackORM.links),
            selectinload(AlbumORM.tracks).selectinload(TrackORM.album),
            selectinload(AlbumORM.artist_rel),
        )
        orm_albums = session.exec(statement).all()
        return [album_from_orm(album) for album in orm_albums]

    def get_all_tracks_storage_links(self, session: Session):
        combined = (TrackLink.link_provider + literal("///") + TrackLink.link).label(
            "combined"
        )
        statement = select(combined).where(TrackLink.link_type == "storage")
        return set(session.exec(statement).all())

    def get_track_by_id(self, session: Session, id: int):
        statement = (
            select(TrackORM)
            .where(TrackORM.id == id)
            .options(
                selectinload(TrackORM.links),
                selectinload(TrackORM.artists),
                selectinload(TrackORM.lyrics),
            )
        )
        orm_track = session.exec(statement).first()
        return track_from_orm(orm_track) if orm_track else None

    def get_album_by_id(self, session: Session, id: int):
        statement = (
            select(AlbumORM)
            .where(AlbumORM.id == id)
            .options(
                selectinload(AlbumORM.tracks).selectinload(TrackORM.links),
                selectinload(AlbumORM.tracks).selectinload(TrackORM.album),
                selectinload(AlbumORM.artist_rel),
            )
        )
        orm_album = session.exec(statement).first()
        return album_from_orm(orm_album) if orm_album else None

    def get_artist_by_id(self, session: Session, id: int):
        statement = (
            select(ArtistORM)
            .where(ArtistORM.id == id)
            .options(
                selectinload(ArtistORM.albums).selectinload(AlbumORM.tracks),
                selectinload(ArtistORM.albums).selectinload(AlbumORM.artist_rel),
            )
        )
        orm_artist = session.exec(statement).first()
        return artist_from_orm(orm_artist) if orm_artist else None
