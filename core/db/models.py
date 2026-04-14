from sqlmodel import (
    SQLModel,
    Field,
    create_engine,
    Session,
    select,
    Relationship,
    literal,
    delete,
    col,
)
from sqlalchemy.ext.hybrid import hybrid_property
from typing import ClassVar
from typing import List, Optional
from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    tuple_,
    func,
    UniqueConstraint,
    CheckConstraint,
    JSON,
)
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone


class PlaylistTrackLink(SQLModel, table=True):
    __tablename__ = "playlist_track_link"
    __table_args__ = (
        UniqueConstraint("playlist_id", "position", name="uq_playlist_position"),
        CheckConstraint("position > 0", name="ck_position_positive"),
    )
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
    track: "TrackORM" = Relationship(back_populates="playlist_links")
    playlist: "PlaylistORM" = Relationship(back_populates="track_links")
    position: int


class ArtistAlias(SQLModel, table=True):
    __tablename__ = "artist_alias"
    id: Optional[int] = Field(default=None, primary_key=True)
    artist_id: int = Field(foreign_key="artist.id", ondelete="CASCADE")
    name: str
    artist: "ArtistORM" = Relationship(back_populates="aliases")


class TrackArtistsLink(SQLModel, table=True):
    __tablename__ = "track_artist"
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
    __tablename__ = "starred_track"
    user_id: int = Field(foreign_key="user.id", primary_key=True)
    track_id: int = Field(foreign_key="track.id", primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    user: "User" = Relationship(back_populates="starred_tracks_link")
    track: "TrackORM" = Relationship(back_populates="starred_track_links")


class StarredAlbum(SQLModel, table=True):
    __tablename__ = "starred_album"
    user_id: int = Field(foreign_key="user.id", primary_key=True)
    album_id: int = Field(foreign_key="album.id", primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    user: "User" = Relationship(back_populates="starred_albums_link")
    album: "AlbumORM" = Relationship(back_populates="starred_album_links")


class StarredArtist(SQLModel, table=True):
    __tablename__ = "starred_artist"
    user_id: int = Field(foreign_key="user.id", primary_key=True)
    artist_id: int = Field(foreign_key="artist.id", primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    user: "User" = Relationship(back_populates="starred_artists_link")
    artist: "ArtistORM" = Relationship(back_populates="starred_artist_links")


class User(SQLModel, table=True):
    __tablename__ = "user"
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True)
    password: str
    email: str
    api_key: Optional[str] = Field(default=None, unique=True, index=True)
    is_admin: bool

    playlists: List["PlaylistORM"] = Relationship(back_populates="owner")

    starred_tracks_link: List["StarredTrack"] = Relationship(back_populates="user")
    starred_albums_link: List["StarredAlbum"] = Relationship(back_populates="user")
    starred_artists_link: List["StarredArtist"] = Relationship(back_populates="user")

    starred_tracks: List["TrackORM"] = Relationship(
        back_populates="starred_by",
        link_model=StarredTrack,
        sa_relationship_kwargs={"viewonly": True},
    )
    starred_albums: List["AlbumORM"] = Relationship(
        back_populates="starred_by",
        link_model=StarredAlbum,
        sa_relationship_kwargs={"viewonly": True},
    )
    starred_artists: List["ArtistORM"] = Relationship(
        back_populates="starred_by",
        link_model=StarredArtist,
        sa_relationship_kwargs={"viewonly": True},
    )


class ArtistORM(SQLModel, table=True):
    __tablename__ = "artist"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    cover_path: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    albums: List["AlbumORM"] = Relationship(
        back_populates="artist_rel",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    tracks: List["TrackORM"] = Relationship(
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
    aliases: List["ArtistAlias"] = Relationship(
        back_populates="artist",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class AlbumORM(SQLModel, table=True):
    __tablename__ = "album"
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    year: Optional[int] = Field(default=None)

    artist_id: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("artist.id", ondelete="CASCADE")),
    )
    cover_path: Optional[str] = Field(default=None)
    artist_rel: Optional[ArtistORM] = Relationship(back_populates="albums")

    tracks: List["TrackORM"] = Relationship(
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
            select(func.sum(TrackORM.length))
            .where(TrackORM.album_id == cls.id)
            .scalar_subquery()
        )

    @hybrid_property
    def track_count(self) -> int:
        return len(self.tracks)

    track_count: ClassVar[hybrid_property]

    @track_count.expression
    def track_count(cls):
        return (
            select(func.count(TrackORM.id))
            .select_from(TrackORM)
            .where(TrackORM.album_id == cls.id)
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


class TrackGenreLink(SQLModel, table=True):
    __tablename__ = "track_genre"
    track_id: Optional[int] = Field(
        default=None, foreign_key="track.id", primary_key=True
    )
    genre_id: Optional[int] = Field(
        default=None, foreign_key="genre.id", primary_key=True
    )


class TrackMoodLink(SQLModel, table=True):
    __tablename__ = "track_mood"
    track_id: Optional[int] = Field(
        default=None, foreign_key="track.id", primary_key=True
    )
    mood_id: Optional[int] = Field(
        default=None, foreign_key="mood.id", primary_key=True
    )


class Genre(SQLModel, table=True):
    __tablename__ = "genre"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True)

    tracks: List["TrackORM"] = Relationship(
        back_populates="genres", link_model=TrackGenreLink
    )


class Mood(SQLModel, table=True):
    __tablename__ = "mood"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True)

    tracks: List["TrackORM"] = Relationship(
        back_populates="moods", link_model=TrackMoodLink
    )


class TrackORM(SQLModel, table=True):
    __tablename__ = "track"
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    length: int
    bpm: Optional[int] = None
    trackGain: Optional[float] = None
    trackPeak: Optional[float] = None
    discNumber: Optional[int] = None
    year: Optional[int] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    album_position: Optional[int]
    album_id: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("album.id", ondelete="CASCADE")),
    )
    album: Optional["AlbumORM"] = Relationship(back_populates="tracks")

    lyrics: List["LyricsORM"] = Relationship(
        back_populates="track",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )

    links: List["TrackLink"] = Relationship(
        back_populates="track",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )

    playlist_links: List["PlaylistTrackLink"] = Relationship(back_populates="track")
    starred_track_links: List["StarredTrack"] = Relationship(back_populates="track")
    starred_by: List["User"] = Relationship(
        back_populates="starred_tracks",
        link_model=StarredTrack,
        sa_relationship_kwargs={
            "overlaps": "starred_track_links,starred_tracks_link,track,user"
        },
    )
    artists: List["ArtistORM"] = Relationship(
        back_populates="tracks", link_model=TrackArtistsLink
    )
    music_videos: List["MusicVideoORM"] = Relationship(back_populates="track")
    genres: List["Genre"] = Relationship(
        back_populates="tracks", link_model=TrackGenreLink
    )
    moods: List["Mood"] = Relationship(
        back_populates="tracks", link_model=TrackMoodLink
    )


class LyricsORM(SQLModel, table=True):
    __tablename__ = "lyrics"
    id: int | None = Field(default=None, primary_key=True)
    is_synced: bool = False
    language: str | None = None
    plain_text: str | None = None
    synced_text: list[dict] | None = Field(default=None, sa_column=Column(JSON))
    type: str | None = None
    offset: int = Field(default=0)
    original_path: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    track_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("track.id", ondelete="CASCADE"),
            nullable=False,
        )
    )
    track: Optional[TrackORM] = Relationship(back_populates="lyrics")


class MusicVideoORM(SQLModel, table=True):
    __tablename__ = "music_video"
    id: Optional[int] = Field(default=None, primary_key=True)
    is_external_link: bool
    external_link: str | None = None
    local_link: str | None = None
    track_id: Optional[int] = Field(
        sa_column=Column(Integer, ForeignKey("track.id", ondelete="CASCADE"))
    )
    track: Optional["TrackORM"] = Relationship(back_populates="music_videos")


class TrackLink(SQLModel, table=True):
    __tablename__ = "track_link"
    id: Optional[int] = Field(default=None, primary_key=True)
    link_type: str
    link_provider: str
    link: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    track_id: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("track.id", ondelete="CASCADE")),
    )
    track: Optional[TrackORM] = Relationship(back_populates="links")


class PlaylistORM(SQLModel, table=True):
    __tablename__ = "playlist"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    cover_path: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_public: bool = Field(default=False)

    owner_id: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("user.id", ondelete="CASCADE")),
    )
    owner: Optional["User"] = Relationship(back_populates="playlists")

    @hybrid_property
    def song_count(self) -> int:
        return len(self.track_links)

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
        return sum(t.track.length for t in self.track_links)

    duration: ClassVar[hybrid_property]

    @duration.expression
    def duration(cls):
        return (
            select(func.sum(TrackORM.length))
            .join(PlaylistTrackLink, PlaylistTrackLink.track_id == TrackORM.id)
            .where(PlaylistTrackLink.playlist_id == cls.id)
            .scalar_subquery()
        )

    track_links: List["PlaylistTrackLink"] = Relationship(back_populates="playlist")


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

    def get_artist_by_name(self, session: Session, name: str) -> Optional[ArtistORM]:
        return session.exec(
            select(ArtistORM)
            .outerjoin(ArtistAlias)
            .where(
                (col(ArtistORM.name).ilike(name)) | (col(ArtistAlias.name).ilike(name))
            )
        ).first()

    def get_album_by_name(self, session: Session, title: str) -> Optional[AlbumORM]:
        return session.exec(select(AlbumORM).where(AlbumORM.title == title)).first()

    def get_moods(self, session: Session) -> List[Mood] | None:
        moods = (
            session.execute(select(Mood).options(selectinload(Mood.tracks)))
            .scalars()
            .all()
        )
        return moods

    def get_genres(self, session: Session) -> List[Genre] | None:
        genres = (
            session.execute(select(Genre).options(selectinload(Genre.tracks)))
            .scalars()
            .all()
        )
        return genres

    def get_track_by_name(self, session: Session, title: str) -> Optional[TrackORM]:
        return session.exec(
            select(TrackORM).where(col(TrackORM.title).ilike(title))
        ).first()

    def get_user_by_name(self, session: Session, username: str) -> Optional[User]:
        return session.exec(select(User).where(User.username == username)).first()

    def get_user_by_id(self, session: Session, id: int) -> Optional[User]:
        return session.exec(select(User).where(User.id == id)).first()

    def get_video_by_id(self, session: Session, id: int):
        return session.exec(select(MusicVideoORM).where(MusicVideoORM.id == id)).first()

    def get_playlist_by_id(self, session: Session, id: int) -> Optional[PlaylistORM]:
        playlist = session.exec(
            select(PlaylistORM)
            .where(PlaylistORM.id == id)
            .options(
                selectinload(PlaylistORM.owner),
                selectinload(PlaylistORM.tracks).selectinload(TrackORM.links),
                selectinload(PlaylistORM.tracks)
                .selectinload(TrackORM.album)
                .selectinload(AlbumORM.artist_rel),
            )
        ).first()
        return playlist

    def get_user_by_apikey(self, session: Session, api_key: str) -> Optional[User]:
        return session.exec(select(User).where(User.api_key == api_key)).first()

    def search_artists(self, session: Session, query: str, limit: int, offset: int):
        artists = session.exec(
            select(ArtistORM)
            .outerjoin(ArtistAlias)
            .where(
                (col(ArtistORM.name).ilike(f"%{query}%"))
                | (col(ArtistAlias.name).ilike(f"%{query}%"))
            )
            .limit(limit)
            .offset(offset)
            .options(selectinload(ArtistORM.albums))
        ).all()
        return artists

    def search_albums(self, session: Session, query: str, limit: int, offset: int):
        return session.exec(
            select(AlbumORM)
            .where(col(AlbumORM.title).ilike(f"%{query}%"))
            .limit(limit)
            .offset(offset)
            .options(
                selectinload(AlbumORM.tracks).selectinload(TrackORM.links),
                selectinload(AlbumORM.tracks).selectinload(TrackORM.album),
                selectinload(AlbumORM.artist_rel),
            )
        ).all()

    def search_tracks(self, session: Session, query: str, limit: int, offset: int):
        tracks = session.exec(
            select(TrackORM)
            .where(col(TrackORM.title).ilike(f"%{query}%"))
            .limit(limit)
            .offset(offset)
            .options(
                selectinload(TrackORM.links),
                selectinload(TrackORM.album).selectinload(AlbumORM.artist_rel),
            )
        ).all()
        return tracks

    def search_playlists(self, session: Session, query: str, limit: int, offset: int):
        playlists = session.exec(
            select(PlaylistORM)
            .where(col(PlaylistORM.name).ilike(f"%{query}%"))
            .limit(limit)
            .offset(offset)
        ).all()
        return playlists

    def get_all_user_starred(self, session: Session, user_id: int):
        user = self.get_user_by_id(session, user_id)
        starred_tracks = user.starred_tracks
        starred_albums = user.starred_albums
        starred_artists = user.starred_artists
        return (starred_tracks, starred_albums, starred_artists)

    def get_user_playlists(self, session: Session, user_id: int):
        playlists = session.exec(
            select(PlaylistORM)
            .where(PlaylistORM.owner_id == user_id)
            .options(selectinload(PlaylistORM.owner), selectinload(PlaylistORM.tracks))
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
            statement = select(TrackORM).where(TrackORM.id == id)
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
            delete_tracks_statement = delete(TrackORM).where(TrackORM.id.in_(track_ids))
            tracks = session.exec(delete_tracks_statement)
            session.commit()
            return tracks.rowcount

    def get_all_tracks(self):
        with Session(self.engine) as session:
            statement = select(TrackORM).options(selectinload(TrackORM.links))
            tracks = session.exec(statement).all()
            return tracks

    def get_all_artists(self):
        with Session(self.engine) as session:
            statement = select(ArtistORM).options(selectinload(ArtistORM.albums))
            tracks = session.exec(statement).all()
            return tracks

    def get_all_albums(self, session: Session):
        statement = select(AlbumORM).options(
            selectinload(AlbumORM.tracks).selectinload(TrackORM.links),
            selectinload(AlbumORM.tracks).selectinload(TrackORM.album),
            selectinload(AlbumORM.artist_rel),
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
                select(TrackORM)
                .where(TrackORM.id == id)
                .options(
                    selectinload(TrackORM.links),
                    selectinload(TrackORM.artists),
                    selectinload(TrackORM.lyrics),
                )
            )
            track = session.exec(statement).first()
            return track

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
        track = session.exec(statement).first()
        return track

    def get_artist_by_id(self, session: Session, id: int):
        statement = (
            select(ArtistORM)
            .where(ArtistORM.id == id)
            .options(
                selectinload(ArtistORM.albums).selectinload(AlbumORM.tracks),
                selectinload(ArtistORM.albums).selectinload(AlbumORM.artist_rel),
            )
        )
        track = session.exec(statement).first()
        return track
