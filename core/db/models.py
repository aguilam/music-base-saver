from sqlmodel import (
    SQLModel,
    Field,
    select,
    Relationship,
)
from sqlalchemy.ext.hybrid import hybrid_property
from typing import ClassVar
from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    func,
    UniqueConstraint,
    CheckConstraint,
    JSON,
)
from datetime import datetime, timezone


class AlbumArtistLink(SQLModel, table=True):
    __tablename__ = "album_artist_link"
    artist_id: int = Field(foreign_key="artist.id", primary_key=True)
    album_id: int = Field(foreign_key="album.id", primary_key=True)


class ArtistGenreLink(SQLModel, table=True):
    __tablename__ = "artist_genre"
    artist_id: int | None = Field(
        default=None, foreign_key="artist.id", primary_key=True
    )
    genre_id: int | None = Field(default=None, foreign_key="genre.id", primary_key=True)


class AlbumGenreLink(SQLModel, table=True):
    __tablename__ = "album_genre"
    album_id: int | None = Field(default=None, foreign_key="album.id", primary_key=True)
    genre_id: int | None = Field(default=None, foreign_key="genre.id", primary_key=True)


class TrackGenreLink(SQLModel, table=True):
    __tablename__ = "track_genre"
    track_id: int | None = Field(default=None, foreign_key="track.id", primary_key=True)
    genre_id: int | None = Field(default=None, foreign_key="genre.id", primary_key=True)


class TrackMoodLink(SQLModel, table=True):
    __tablename__ = "track_mood"
    track_id: int | None = Field(default=None, foreign_key="track.id", primary_key=True)
    mood_id: int | None = Field(default=None, foreign_key="mood.id", primary_key=True)


class PlaylistTrackLink(SQLModel, table=True):
    __tablename__ = "playlist_track_link"
    __table_args__ = (
        UniqueConstraint("playlist_id", "position", name="uq_playlist_position"),
        CheckConstraint("position > 0", name="ck_position_positive"),
    )
    playlist_id: int | None = Field(
        default=None,
        sa_column=Column(
            Integer, ForeignKey("playlist.id", ondelete="CASCADE"), primary_key=True
        ),
    )
    track_id: int | None = Field(
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
    id: int | None = Field(default=None, primary_key=True)
    artist_id: int = Field(foreign_key="artist.id", ondelete="CASCADE")
    name: str
    artist: "ArtistORM" = Relationship(back_populates="aliases")


class TrackArtistsLink(SQLModel, table=True):
    __tablename__ = "track_artist"
    artist_id: int | None = Field(
        default=None,
        sa_column=Column(
            Integer, ForeignKey("artist.id", ondelete="CASCADE"), primary_key=True
        ),
    )
    track_id: int | None = Field(
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

    user: "UserORM" = Relationship(back_populates="starred_tracks_link")
    track: "TrackORM" = Relationship(back_populates="starred_track_links")


class StarredAlbum(SQLModel, table=True):
    __tablename__ = "starred_album"
    user_id: int = Field(foreign_key="user.id", primary_key=True)
    album_id: int = Field(foreign_key="album.id", primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    user: "UserORM" = Relationship(back_populates="starred_albums_link")
    album: "AlbumORM" = Relationship(back_populates="starred_album_links")


class StarredArtist(SQLModel, table=True):
    __tablename__ = "starred_artist"
    user_id: int = Field(foreign_key="user.id", primary_key=True)
    artist_id: int = Field(foreign_key="artist.id", primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    user: "UserORM" = Relationship(back_populates="starred_artists_link")
    artist: "ArtistORM" = Relationship(back_populates="starred_artist_links")


class PlaylistOwnerORM(SQLModel, table=True):
    __tablename__ = "playlist_owner"
    owner_id: int = Field(foreign_key="user.id", primary_key=True)
    playlist_id: int = Field(foreign_key="playlist.id", primary_key=True)


class UserORM(SQLModel, table=True):
    __tablename__ = "user"
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True)
    password: str
    email: str
    is_admin: bool = False

    api_keys: list["ApiKeyORM"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"passive_deletes": True},
    )
    playlists: list["PlaylistORM"] = Relationship(
        back_populates="owners", link_model=PlaylistOwnerORM
    )

    starred_tracks_link: list["StarredTrack"] = Relationship(back_populates="user")
    starred_albums_link: list["StarredAlbum"] = Relationship(back_populates="user")
    starred_artists_link: list["StarredArtist"] = Relationship(back_populates="user")

    starred_tracks: list["TrackORM"] = Relationship(
        back_populates="starred_by",
        link_model=StarredTrack,
        sa_relationship_kwargs={"viewonly": True},
    )
    starred_albums: list["AlbumORM"] = Relationship(
        back_populates="starred_by",
        link_model=StarredAlbum,
        sa_relationship_kwargs={"viewonly": True},
    )
    starred_artists: list["ArtistORM"] = Relationship(
        back_populates="starred_by",
        link_model=StarredArtist,
        sa_relationship_kwargs={"viewonly": True},
    )


class TrackAlbumLink(SQLModel, table=True):
    __tablename__ = "track_album"
    track_id: int = Field(primary_key=True, foreign_key="track.id")
    album_id: int = Field(primary_key=True, foreign_key="album.id")
    album_position: int
    disc_number: int | None = None
    is_primary_album: bool = False
    track: "TrackORM" = Relationship(back_populates="albums_links")
    album: "AlbumORM" = Relationship(back_populates="tracks_links")


class ArtistORM(SQLModel, table=True):
    __tablename__ = "artist"
    id: int | None = Field(default=None, primary_key=True)
    name: str
    cover_path: int | None = Field(default=None, foreign_key="object_storage.id")
    description: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    albums: list["AlbumORM"] = Relationship(
        back_populates="artists",
        link_model=AlbumArtistLink,
    )
    tracks: list["TrackORM"] = Relationship(
        back_populates="artists", link_model=TrackArtistsLink
    )
    genres: list["GenreORM"] = Relationship(
        back_populates="artists", link_model=ArtistGenreLink
    )
    starred_artist_links: list[StarredArtist] = Relationship(back_populates="artist")
    starred_by: list["UserORM"] = Relationship(
        back_populates="starred_artists",
        link_model=StarredArtist,
        sa_relationship_kwargs={
            "overlaps": "starred_artist_links,starred_artists_link,artist,user"
        },
    )
    aliases: list["ArtistAlias"] = Relationship(
        back_populates="artist",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class AlbumORM(SQLModel, table=True):
    __tablename__ = "album"
    id: int | None = Field(default=None, primary_key=True)
    title: str
    type: str | None = None
    year: int | None = Field(default=None)
    cover_path: int | None = Field(default=None, foreign_key="object_storage.id")
    artists: list[ArtistORM] = Relationship(
        back_populates="albums", link_model=AlbumArtistLink
    )
    genres: list["GenreORM"] = Relationship(
        back_populates="albums", link_model=AlbumGenreLink
    )
    description: str | None = None
    tracks_links: list["TrackAlbumLink"] = Relationship(
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

    starred_album_links: list[StarredAlbum] = Relationship(back_populates="album")
    starred_by: list["UserORM"] = Relationship(
        back_populates="starred_albums",
        link_model=StarredAlbum,
        sa_relationship_kwargs={
            "overlaps": "starred_album_links,starred_albums_link,album,user"
        },
    )


class GenreORM(SQLModel, table=True):
    __tablename__ = "genre"
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True)

    artists: list["ArtistORM"] = Relationship(
        back_populates="genres", link_model=ArtistGenreLink
    )
    albums: list["AlbumORM"] = Relationship(
        back_populates="genres", link_model=AlbumGenreLink
    )
    tracks: list["TrackORM"] = Relationship(
        back_populates="genres", link_model=TrackGenreLink
    )


class MoodORM(SQLModel, table=True):
    __tablename__ = "mood"
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True)

    tracks: list["TrackORM"] = Relationship(
        back_populates="moods", link_model=TrackMoodLink
    )


class ObjectStorageORM(SQLModel, table=True):
    __tablename__ = "object_storage"
    id: int | None = Field(default=None, primary_key=True)
    link_type: str
    link_provider: str
    link: str
    file_name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    audio_id: int | None = Field(default=None, foreign_key="audio_file.id")
    music_video_id: int | None = Field(default=None, foreign_key="music_video.id")
    lyrics_id: int | None = Field(default=None, foreign_key="lyrics.id")


class AudioFileORM(SQLModel, table=True):
    __tablename__ = "audio_file"
    id: int | None = Field(default=None, primary_key=True)
    file_size: int | None = None
    hash: str | None = None
    is_primary: bool = False
    bitrate: int | None = None
    bit_depth: int | None = None
    sample_rate: int | None = None
    trackGain: float | None = None
    trackPeak: float | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    track_id: int = Field(foreign_key="track.id")
    links: list["ObjectStorageORM"] = Relationship(
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "foreign_keys": ObjectStorageORM.audio_id,
        },
    )


class TrackORM(SQLModel, table=True):
    __tablename__ = "track"
    id: int | None = Field(default=None, primary_key=True)
    title: str
    length: int
    bpm: int | None = None
    year: int | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    albums_links: list[TrackAlbumLink] = Relationship(back_populates="track")

    lyrics: list["LyricsORM"] = Relationship(
        back_populates="track",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )

    files: list["AudioFileORM"] = Relationship(
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "foreign_keys": AudioFileORM.track_id,
        },
    )

    playlist_links: list["PlaylistTrackLink"] = Relationship(back_populates="track")
    starred_track_links: list["StarredTrack"] = Relationship(back_populates="track")
    starred_by: list["UserORM"] = Relationship(
        back_populates="starred_tracks",
        link_model=StarredTrack,
        sa_relationship_kwargs={
            "overlaps": "starred_track_links,starred_tracks_link,track,user"
        },
    )
    artists: list["ArtistORM"] = Relationship(
        back_populates="tracks", link_model=TrackArtistsLink
    )
    music_videos: list["MusicVideoORM"] = Relationship(back_populates="track")
    genres: list["GenreORM"] = Relationship(
        back_populates="tracks", link_model=TrackGenreLink
    )
    moods: list["MoodORM"] = Relationship(
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
    path: list["ObjectStorageORM"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": ObjectStorageORM.lyrics_id},
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    track_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("track.id", ondelete="CASCADE"),
            nullable=False,
        )
    )
    track: TrackORM | None = Relationship(back_populates="lyrics")


class MusicVideoORM(SQLModel, table=True):
    __tablename__ = "music_video"
    id: int | None = Field(default=None, primary_key=True)
    is_external_link: bool = False
    duration_ms: int | None = None
    external_link: str | None = None
    local_link: list["ObjectStorageORM"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": ObjectStorageORM.music_video_id}
    )
    track_id: int | None = Field(
        sa_column=Column(Integer, ForeignKey("track.id", ondelete="CASCADE"))
    )
    track: TrackORM | None = Relationship(back_populates="music_videos")


class PlaylistORM(SQLModel, table=True):
    __tablename__ = "playlist"
    id: int | None = Field(default=None, primary_key=True)
    name: str
    cover_path: int | None = Field(default=None, foreign_key="object_storage.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_public: bool = Field(default=False)

    owners: list[UserORM] = Relationship(
        back_populates="playlists", link_model=PlaylistOwnerORM
    )

    @hybrid_property
    def track_count(self) -> int:
        return len(self.track_links)

    track_count: ClassVar[hybrid_property]

    @track_count.expression
    def track_count(cls):
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

    track_links: list["PlaylistTrackLink"] = Relationship(back_populates="playlist")


class ProviderKeyORM(SQLModel, table=True):
    __tablename__ = "provider_key"
    id: int | None = Field(default=None, primary_key=True)
    provider: str
    key: str
    user_id: int = Field(foreign_key="user.id", ondelete="CASCADE")


class ApiKeyORM(SQLModel, table=True):
    __tablename__ = "api_key"
    id: int | None = Field(default=None, primary_key=True)
    key: str = Field(default=None, unique=True)
    user_id: int = Field(foreign_key="user.id", ondelete="CASCADE")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    revoked: bool = False
    user: UserORM = Relationship(back_populates="api_keys")
