from sqlmodel import (
    SQLModel,
    Field,
    create_engine,
    Session,
    select,
    Relationship,
    literal,
    delete,
)
from sqlalchemy.ext.hybrid import hybrid_property
from typing import ClassVar
from typing import List, Optional
from sqlalchemy import Column, Integer, ForeignKey, tuple_, func, UniqueConstraint
from sqlalchemy.orm import selectinload

from datetime import datetime, timezone


class PlaylistTrackLink(SQLModel, table=True):
    playlist_id: Optional[int] = Field(
        default=None,
        sa_column=Column(
            Integer, ForeignKey("playlist.id", ondelete="CASCADE"), primary_key=True
        ),
    )
    track_id: Optional[int] = Field(
        default=None,
        sa_column=Column(
            Integer, ForeignKey("track.id", ondelete="CASCADE"), primary_key=True
        ),
    )


class TrackArtistsLink(SQLModel, table=True):
    artist_id: Optional[int] = Field(
        default=None,
        sa_column=Column(
            Integer, ForeignKey("artist.id", ondelete="CASCADE"), primary_key=True
        ),
    )
    track_id: Optional[int] = Field(
        default=None,
        sa_column=Column(
            Integer, ForeignKey("track.id", ondelete="CASCADE"), primary_key=True
        ),
    )


class StarredTrack(SQLModel, table=True):
    user_id: int = Field(foreign_key="user.id", primary_key=True)
    track_id: int = Field(foreign_key="track.id", primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    user: "User" = Relationship(back_populates="starred_tracks_link")
    track: "Track" = Relationship(back_populates="starred_track_links")


class StarredAlbum(SQLModel, table=True):
    user_id: int = Field(foreign_key="user.id", primary_key=True)
    album_id: int = Field(foreign_key="album.id", primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    user: "User" = Relationship(back_populates="starred_albums_link")
    album: "Album" = Relationship(back_populates="starred_album_links")


class StarredArtist(SQLModel, table=True):
    user_id: int = Field(foreign_key="user.id", primary_key=True)
    artist_id: int = Field(foreign_key="artist.id", primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    user: "User" = Relationship(back_populates="starred_artists_link")
    artist: "Artist" = Relationship(back_populates="starred_artist_links")


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True)
    password: str
    email: str
    api_key: Optional[str] = Field(default=None, unique=True, index=True)
    is_admin: bool

    playlists: List["Playlist"] = Relationship(back_populates="owner")

    starred_tracks_link: List["StarredTrack"] = Relationship(back_populates="user")
    starred_albums_link: List["StarredAlbum"] = Relationship(back_populates="user")
    starred_artists_link: List["StarredArtist"] = Relationship(back_populates="user")

    starred_tracks: List["Track"] = Relationship(
        back_populates="starred_by",
        link_model=StarredTrack,
        sa_relationship_kwargs={"viewonly": True},
    )
    starred_albums: List["Album"] = Relationship(
        back_populates="starred_by",
        link_model=StarredAlbum,
        sa_relationship_kwargs={"viewonly": True},
    )
    starred_artists: List["Artist"] = Relationship(
        back_populates="starred_by",
        link_model=StarredArtist,
        sa_relationship_kwargs={"viewonly": True},
    )


class Artist(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    cover_path: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    albums: List["Album"] = Relationship(
        back_populates="artist_rel",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    tracks: List["Track"] = Relationship(
        back_populates="artists", link_model=TrackArtistsLink
    )
    starred_artist_links: List[StarredArtist] = Relationship(back_populates="artist")
    starred_by: List["User"] = Relationship(
        back_populates="starred_artists",
        link_model=StarredArtist,
        sa_relationship_kwargs={
            "overlaps": "starred_artist_links,starred_artists_link,artist,user"
        },
    )


class Album(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    year: Optional[int] = Field(default=None)

    artist_id: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("artist.id", ondelete="CASCADE")),
    )
    cover_path: Optional[str] = Field(default=None)
    artist_rel: Optional[Artist] = Relationship(back_populates="albums")

    tracks: List["Track"] = Relationship(
        back_populates="album",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @hybrid_property
    def duration(self) -> int:
        return sum(t.length for t in self.tracks)

    duration: ClassVar[hybrid_property]

    @duration.expression
    def duration(cls):
        return (
            select(func.sum(Track.length))
            .where(Track.album_id == cls.id)
            .scalar_subquery()
        )

    starred_album_links: List[StarredAlbum] = Relationship(back_populates="album")
    starred_by: List["User"] = Relationship(
        back_populates="starred_albums",
        link_model=StarredAlbum,
        sa_relationship_kwargs={
            "overlaps": "starred_album_links,starred_albums_link,album,user"
        },
    )


class Track(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    length: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    album_id: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("album.id", ondelete="CASCADE")),
    )
    album: Optional["Album"] = Relationship(back_populates="tracks")

    lyrics: Optional["Lyrics"] = Relationship(
        back_populates="track",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "uselist": False},
    )

    links: List["TrackLink"] = Relationship(
        back_populates="track",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )

    playlists: List["Playlist"] = Relationship(
        back_populates="tracks", link_model=PlaylistTrackLink
    )
    starred_track_links: List[StarredTrack] = Relationship(back_populates="track")
    starred_by: List["User"] = Relationship(
        back_populates="starred_tracks",
        link_model=StarredTrack,
        sa_relationship_kwargs={
            "overlaps": "starred_track_links,starred_tracks_link,track,user"
        },
    )
    artists: List["Artist"] = Relationship(
        back_populates="tracks", link_model=TrackArtistsLink
    )


class Lyrics(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    value: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    track_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("track.id", ondelete="CASCADE"),
            unique=True,
            nullable=False,
        )
    )
    track: Optional[Track] = Relationship(back_populates="lyrics")


class TrackLink(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    link_type: str
    link_provider: str
    link: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    track_id: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("track.id", ondelete="CASCADE")),
    )
    track: Optional[Track] = Relationship(back_populates="links")


class Playlist(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    owner: str
    cover_path: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    public: bool = Field(default=False)

    owner_id: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("user.id", ondelete="CASCADE")),
    )
    owner: Optional[User] = Relationship(back_populates="playlists")

    @hybrid_property
    def song_count(self) -> int:
        return len(self.tracks)

    song_count: ClassVar[hybrid_property]

    @song_count.expression
    def song_count(cls):
        return (
            select(func.count())
            .select_from(PlaylistTrackLink)
            .where(PlaylistTrackLink.playlist_id == cls.id)
            .scalar_subquery()
        )

    @hybrid_property
    def duration(self) -> int:
        return sum(t.length for t in self.tracks)

    duration: ClassVar[hybrid_property]

    @duration.expression
    def duration(cls):
        return (
            select(func.sum(Track.length))
            .join(PlaylistTrackLink, PlaylistTrackLink.track_id == Track.id)
            .where(PlaylistTrackLink.playlist_id == cls.id)
            .scalar_subquery()
        )

    tracks: List[Track] = Relationship(
        back_populates="playlists", link_model=PlaylistTrackLink
    )


def admin_create(engine):
    with Session(engine) as session:
        statement = select(func.count()).select_from(User)
        users_count = session.exec(statement).one()
        if users_count < 1:
            admin = User(
                username="admin",
                password="admin",
                email="admin@mail.com",
                is_admin=True,
            )
            session.add(admin)
            session.commit()


class DBManager:
    def __init__(self) -> None:
        self.engine = create_engine("sqlite:///database.db")
        SQLModel.metadata.create_all(self.engine)
        admin_create(self.engine)

    def get_session(self) -> Session:
        return Session(self.engine)

    def get_artist_by_name(self, session: Session, name: str) -> Optional[Artist]:
        return session.exec(select(Artist).where(Artist.name == name)).first()

    def get_album_by_name(self, session: Session, title: str) -> Optional[Album]:
        return session.exec(select(Album).where(Album.title == title)).first()

    def get_track_by_name(self, session: Session, title: str) -> Optional[Track]:
        return session.exec(select(Track).where(Track.title == title)).first()

    def get_user_by_name(self, session: Session, username: str) -> Optional[User]:
        return session.exec(select(User).where(User.username == username)).first()

    def get_user_by_id(self, session: Session, id: int) -> Optional[User]:
        return session.exec(select(User).where(User.id == id)).first()

    def get_playlist_by_id(self, session: Session, id: int) -> Optional[Playlist]:
        playlist = session.exec(
            select(Playlist)
            .where(Playlist.id == id)
            .options(
                selectinload(Playlist.owner),
                selectinload(Playlist.tracks).selectinload(Track.links),
                selectinload(Playlist.tracks)
                .selectinload(Track.album)
                .selectinload(Album.artist_rel),
            )
        ).first()
        return playlist

    def get_user_by_apikey(self, session: Session, api_key: str) -> Optional[User]:
        return session.exec(select(User).where(User.api_key == api_key)).first()

    def get_all_user_starred(self, session: Session, user_id: int):
        user = self.get_user_by_id(session, user_id)
        starred_tracks = user.starred_tracks
        starred_albums = user.starred_albums
        starred_artists = user.starred_artists
        return (starred_tracks, starred_albums, starred_artists)

    def get_user_playlists(self, session: Session, user_id: int):
        playlists = session.exec(
            select(Playlist)
            .where(Playlist.owner_id == user_id)
            .options(selectinload(Playlist.owner), selectinload(Playlist.tracks))
        ).all()
        for p in playlists:
            session.expunge(p)
        return playlists

    def add(self, session: Session, obj):
        session.add(obj)
        session.flush()
        return obj

    def delete_track(self, id: int):
        with Session(self.engine) as session:
            statement = select(Track).where(Track.id == id)
            track = session.exec(statement).first()
            session.delete(track)
            return track

    def bulk_delete_by_links(self, provider_link: list[tuple[str, str]]):
        with Session(self.engine) as session:
            select_ids = select(TrackLink.id, TrackLink.track_id).where(
                tuple_(TrackLink.link_provider, TrackLink.link).in_(provider_link)
            )
            ids_statement = session.exec(select_ids).all()
            links_ids = [r[0] for r in ids_statement]
            track_ids = [r[1] for r in ids_statement]
            delete_links_statement = delete(TrackLink).where(
                TrackLink.id.in_(links_ids)
            )
            session.exec(delete_links_statement)
            delete_tracks_statement = delete(Track).where(Track.id.in_(track_ids))
            tracks = session.exec(delete_tracks_statement)
            session.commit()
            return tracks.rowcount

    def get_all_tracks(self):
        with Session(self.engine) as session:
            statement = select(Track).options(selectinload(Track.links))
            tracks = session.exec(statement).all()
            return tracks

    def get_all_artists(self):
        with Session(self.engine) as session:
            statement = select(Artist).options(selectinload(Artist.albums))
            tracks = session.exec(statement).all()
            return tracks

    def get_all_albums(self, session: Session):
        statement = select(Album).options(
            selectinload(Album.tracks).selectinload(Track.links),
            selectinload(Album.tracks).selectinload(Track.album),
            selectinload(Album.artist_rel),
        )
        albums = session.exec(statement).all()
        return albums

    def get_all_tracks_storage_links(self):
        with Session(self.engine) as session:
            combined = (
                TrackLink.link_provider + literal("///") + TrackLink.link
            ).label("combined")
            statement = select(combined).where(TrackLink.link_type == "storage")
            return set(session.exec(statement).all())

    def get_track_by_id(self, id: int):
        with Session(self.engine) as session:
            statement = (
                select(Track).where(Track.id == id).options(selectinload(Track.links))
            )
            track = session.exec(statement).first()
            return track

    def get_album_by_id(self, session: Session, id: int):
        statement = (
            select(Album)
            .where(Album.id == id)
            .options(
                selectinload(Album.tracks).selectinload(Track.links),
                selectinload(Album.tracks).selectinload(Track.album),
                selectinload(Album.artist_rel),
            )
        )
        track = session.exec(statement).first()
        return track

    def get_artist_by_id(self, session: Session, id: int):
        statement = (
            select(Artist)
            .where(Artist.id == id)
            .options(
                selectinload(Artist.albums).selectinload(Album.tracks),
                selectinload(Artist.albums).selectinload(Album.artist_rel),
            )
        )
        track = session.exec(statement).first()
        return track
