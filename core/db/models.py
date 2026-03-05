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

from typing import List, Optional
from sqlalchemy import Column, Integer, ForeignKey, tuple_, func
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


class Artist(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    cover_path: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    albums: List["Album"] = Relationship(
        back_populates="artist_rel",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
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

    @duration.expression
    def duration(cls):
        return (
            select(func.sum(Track.length))
            .where(Track.album_id == cls.id)
            .scalar_subquery()
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
    album: Optional[Album] = Relationship(back_populates="tracks")

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
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    public: bool = Field(default=True)

    tracks: List[Track] = Relationship(
        back_populates="playlists", link_model=PlaylistTrackLink
    )


class DBManager:
    def __init__(self) -> None:
        self.engine = create_engine("sqlite:///database.db")
        SQLModel.metadata.create_all(self.engine)

    def get_session(self) -> Session:
        return Session(self.engine)

    def get_artist_by_name(self, session: Session, name: str) -> Optional[Artist]:
        return session.exec(select(Artist).where(Artist.name == name)).first()

    def get_album_by_name(self, session: Session, title: str) -> Optional[Album]:
        return session.exec(select(Album).where(Album.title == title)).first()

    def get_track_by_name(self, session: Session, title: str) -> Optional[Track]:
        with Session(self.engine) as session:
            return session.exec(select(Track).where(Track.title == title)).first()

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

    def get_all_albums(self):
        with Session(self.engine) as session:
            statement = select(Artist).options(selectinload(Album.tracks))
            tracks = session.exec(statement).all()
            return tracks

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

    def get_album_by_id(self, id: int):
        with Session(self.engine) as session:
            statement = (
                select(Album).where(Album.id == id).options(selectinload(Album.tracks))
            )
            track = session.exec(statement).first()
            return track

    def get_artist_by_id(self, id: int):
        with Session(self.engine) as session:
            statement = (
                select(Artist)
                .where(Artist.id == id)
                .options(selectinload(Artist.albums))
            )
            track = session.exec(statement).first()
            return track
