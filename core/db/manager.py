from __future__ import annotations
from typing import TYPE_CHECKING, cast, Any
from sqlmodel import (
    SQLModel,
    create_engine,
    Session,
    select,
    update,
    literal,
    delete,
    col,
)
from core.errors import NotFoundError, ForbiddenError, BaseError
from core.utils import decode_cursor, encode_cursor
from sqlalchemy import tuple_, or_, func, distinct, and_
from core.db.mappers import (
    artist_from_orm,
    album_from_orm,
    playlist_from_orm,
    track_from_orm,
    music_video_from_orm,
    user_from_orm,
    stored_user_from_orm,
    object_storage_from_orm,
    mood_from_orm,
    genre_from_orm,
    provider_key_from_orm,
    api_key_from_orm,
    listed_user_from_orm,
)
from core.db.models import (
    UserORM,
    ArtistAlias,
    ArtistORM,
    AlbumORM,
    GenreORM,
    MoodORM,
    ObjectStorageORM,
    TrackORM,
    PlaylistORM,
    MusicVideoORM,
    ApiKeyORM,
    StoredUserORM,
    ProviderKeyORM,
    PlaylistTrackLink,
    AudioFileORM,
    AlbumGenreLink,
    TrackGenreLink,
    ArtistGenreLink,
    TrackMoodLink,
    TrackAlbumLink,
    LyricsORM,
    AlbumArtistLink,
    TrackArtistsLink,
)
from sqlalchemy.orm import selectinload, InstrumentedAttribute

if TYPE_CHECKING:
    from core.schemas.schemas import (
        ApiKey,
        Album,
        Artist,
        Track,
        Playlist,
        StoredUser,
        Mood,
        Genre,
        User,
        MusicVideo,
        ObjectStorage,
        ProviderKey,
        ListedUserResponse,
    )


def in_load_typing(value) -> InstrumentedAttribute[Any]:
    return cast(InstrumentedAttribute[Any], value)


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


class DBManager:
    def __init__(self) -> None:
        self.engine = create_engine("sqlite:///database.db")
        SQLModel.metadata.create_all(self.engine)
        admin_create(self.engine)

    def get_session(self) -> Session:
        return Session(self.engine)

    def get_artist_by_name(self, session: Session, name: str) -> Artist | None:
        orm_artist = session.exec(
            select(ArtistORM)
            .outerjoin(ArtistAlias)
            .where(
                (col(ArtistORM.name).ilike(name)) | (col(ArtistAlias.name).ilike(name))
            )
        ).first()
        return artist_from_orm(orm_artist) if orm_artist else None

    def get_album_by_name(self, session: Session, title: str) -> Album | None:
        album = session.exec(
            select(AlbumORM).where(col(AlbumORM.title) == title)
        ).first()
        return album_from_orm(album) if album else None

    def get_tracks_by_artist_name(self, session: Session, artist_name: str):
        tracks = session.exec(
            select(TrackORM)
            .join(col(TrackORM.artists))
            .where(ArtistORM.name == artist_name)
        ).all()
        return [track_from_orm(track) for track in tracks]

    def get_all_users(self, session: Session) -> list[ListedUserResponse]:
        statement = select(UserORM)
        users = session.exec(statement)
        return [
            listed_user_from_orm(StoredUserORM.model_validate(user)) for user in users
        ]

    def get_provider_key(
        self, session: Session, provider: str, user_id: int
    ) -> ProviderKey | None:
        statement = select(ProviderKeyORM).where(
            ProviderKeyORM.provider == provider, ProviderKeyORM.user_id == user_id
        )
        key = session.exec(statement).first()
        return provider_key_from_orm(key) if key else None

    def change_provider_key(self, session: Session, id: int, new_value: str):
        session.exec(
            update(ProviderKeyORM)
            .where(col(ProviderKeyORM.id) == id)
            .values(key=new_value)
        )
        session.flush()

    def create_provider_key(
        self, session: Session, user_id: int, key: str, provider: str
    ) -> ProviderKey:
        provider_key = ProviderKeyORM(user_id=user_id, key=key, provider=provider)
        session.add(provider_key)
        session.flush()
        return provider_key_from_orm(provider_key)

    def delete_provider_key(self, session: Session, id: int):
        session.exec(delete(ProviderKeyORM).where(col(ProviderKeyORM.id) == id))
        session.flush()

    def get_user_provider_keys(
        self, session: Session, user_id: int
    ) -> list[ProviderKey]:
        statement = select(ProviderKeyORM).where(ProviderKeyORM.user_id == user_id)
        keys = session.exec(statement).all()
        return [provider_key_from_orm(key) for key in keys]

    def get_user_api_keys(self, session: Session, user_id: int):
        statement = select(ApiKeyORM).where(ApiKeyORM.user_id == user_id)
        keys = session.exec(statement).all()
        return [api_key_from_orm(key) for key in keys]

    def check_api_key_availability(
        self, session: Session, api_key: str
    ) -> ApiKey | None:
        key = session.exec(
            select(ApiKeyORM).where(ApiKeyORM.key == api_key, ~col(ApiKeyORM.revoked))
        ).first()
        return api_key_from_orm(key) if key else None

    def create_api_key(self, session: Session, user_id: int, key: str) -> ApiKey:
        api_key = ApiKeyORM(user_id=user_id, key=key)
        session.add(api_key)
        session.flush()
        return api_key_from_orm(api_key)

    def revoke_api_key(self, session: Session, id: int):
        session.exec(
            update(ApiKeyORM).where(col(ApiKeyORM.id) == id).values(revoked=True)
        )
        session.flush()

    def get_moods(self, session: Session) -> list[Mood]:
        moods = session.exec(
            select(MoodORM).options(selectinload(in_load_typing(MoodORM.tracks)))
        ).all()
        return [mood_from_orm(mood) for mood in moods]

    def get_genres(self, session: Session) -> list[Genre]:
        genres = session.exec(
            select(GenreORM).options(selectinload(in_load_typing(GenreORM.tracks)))
        ).all()
        return [genre_from_orm(genre) for genre in genres]

    def get_storage_object_by_id(
        self, session: Session, id: int
    ) -> ObjectStorage | None:
        storage = session.exec(
            select(ObjectStorageORM).where(ObjectStorageORM.id == id)
        ).first()

        return object_storage_from_orm(storage) if storage else None

    def get_track_by_name(self, session: Session, title: str) -> Track | BaseError:
        orm_track = session.exec(
            select(TrackORM).where(col(TrackORM.title).ilike(title))
        ).first()
        return track_from_orm(orm_track) if orm_track else NotFoundError()

    def get_user_by_name(
        self, session: Session, username: str
    ) -> StoredUser | BaseError:
        orm_user = session.exec(
            select(UserORM).where(UserORM.username == username)
        ).first()
        return (
            stored_user_from_orm(StoredUserORM.model_validate(orm_user))
            if orm_user
            else NotFoundError()
        )

    def find_or_create_artist(self, session: Session, name: str) -> ArtistORM:
        normalized_name = name.lower().strip()

        existed_artist = session.exec(
            select(ArtistORM).where(
                or_(
                    col(ArtistORM.normalized_name) == normalized_name,
                    col(ArtistORM.aliases).any(
                        col(ArtistAlias.normalized_name) == normalized_name
                    ),
                )
            )
        ).first()
        if existed_artist:
            return existed_artist
        new_artist = ArtistORM(name=name, normalized_name=normalized_name)
        session.add(new_artist)
        session.flush()
        return new_artist

    def find_or_create_album(
        self,
        session: Session,
        title: str,
        artists_names: list[str] | None = None,
        year: int | None = None,
        description: str | None = None,
        type: str | None = None,
    ) -> AlbumORM:
        normalized_title = title.lower().strip()
        stmt = select(AlbumORM).where(AlbumORM.normalized_title == normalized_title)
        if artists_names:
            stmt = (
                stmt.join(col(AlbumORM.artists))
                .where(col(ArtistORM.name).in_(artists_names))
                .distinct()
            )
        existed_album = session.exec(stmt).first()
        if existed_album:
            return existed_album
        new_album = AlbumORM(
            title=title,
            normalized_title=normalized_title,
            year=year,
            description=description,
            type=type,
        )
        session.add(new_album)
        session.flush()
        return new_album

    def find_or_create_mood(self, session: Session, mood_name: str) -> MoodORM:
        normalized_name = mood_name.lower().strip()
        mood = session.exec(
            select(MoodORM).where(MoodORM.normalized_name == normalized_name)
        ).first()
        if mood:
            return mood
        new_mood = MoodORM(name=mood_name.strip(), normalized_name=normalized_name)
        session.add(new_mood)
        session.flush()
        return new_mood

    def find_or_create_genre(self, session: Session, genre_name: str) -> GenreORM:
        normalized_name = genre_name.lower().strip()
        genre = session.exec(
            select(GenreORM).where(GenreORM.normalized_name == normalized_name)
        ).first()
        if genre:
            return genre
        new_genre = GenreORM(name=genre_name.strip(), normalized_name=normalized_name)
        session.add(new_genre)
        session.flush()
        return new_genre

    def get_user_by_id(self, session: Session, id: int) -> StoredUser | None:
        orm_user = session.exec(select(UserORM).where(UserORM.id == id)).first()
        return (
            stored_user_from_orm(StoredUserORM.model_validate(orm_user))
            if orm_user
            else None
        )

    def get_video_by_id(self, session: Session, id: int) -> MusicVideo | None:
        orm_video = session.exec(
            select(MusicVideoORM).where(MusicVideoORM.id == id)
        ).first()
        return music_video_from_orm(orm_video) if orm_video else None

    def get_playlist_by_id(self, session: Session, id: int) -> Playlist | NotFoundError:
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
                .selectinload(in_load_typing(AlbumORM.artists)),
            )
        )
        orm_playlist = session.exec(statement).first()
        return playlist_from_orm(orm_playlist) if orm_playlist else NotFoundError()

    def update_playlist(
        self,
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
            old_tracks = [link.track_id for link in playlist.track_links]
            new_tracks: list[PlaylistTrackLink] = []
            for track_id in track_ids:
                if track_id not in old_tracks:
                    track_link = PlaylistTrackLink(
                        playlist_id=playlist.id, track_id=track_id
                    )
                    new_tracks.append(track_link)
                    continue
                new_tracks.append(
                    next(
                        link
                        for link in playlist.track_links
                        if link.track_id == track_id
                    )
                )
            playlist.track_links = new_tracks
        session.flush()
        return playlist_from_orm(playlist)

    def create_user(
        self, session: Session, username: str, email: str, password: str
    ) -> ListedUserResponse:
        new_user = UserORM(username=username, email=email, password=password)
        session.add(new_user)
        session.flush()
        return listed_user_from_orm(StoredUserORM.model_validate(new_user))

    def update_user(
        self,
        session: Session,
        user_id: int,
        username: str | None,
        password: str | None,
        is_admin: bool | None,
    ) -> User | BaseError:
        changed_user = session.exec(
            select(UserORM).where(UserORM.username == username)
        ).first()
        if changed_user is None:
            return NotFoundError()
        same_user = changed_user.id == user_id
        is_changing_admin = changed_user.is_admin
        if not same_user:
            user = session.exec(select(UserORM).where(UserORM.id == user_id)).first()
            if user and user.is_admin:
                is_changing_admin = True
            else:
                return ForbiddenError()
        if is_admin is not None and is_changing_admin:
            changed_user.is_admin = is_admin
        if password and password is not changed_user.password:
            changed_user.password = password
        if username and username is not changed_user.username:
            changed_user.username = username
        return user_from_orm(changed_user)

    def delete_playlist(self, session: Session, id: int):
        statement = delete(PlaylistORM).where(col(PlaylistORM.id) == id)
        session.exec(statement).first()

    def create_playlist(
        self,
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
            title=title, cover_path=cover_path, is_public=is_public, owner=user
        )
        session.add(playlist)
        session.flush()
        for position, track_id in enumerate(tracks_id, start=1):
            trackLink = PlaylistTrackLink(playlist.id, track_id, position=position)
            playlist.track_links.append(trackLink)
        return playlist_from_orm(playlist)

    def get_user_by_apikey(self, session: Session, api_key: str) -> StoredUser | None:
        orm_user = session.exec(
            select(UserORM).join(col(UserORM.api_keys)).where(ApiKeyORM.key == api_key)
        ).first()
        return (
            stored_user_from_orm(StoredUserORM.model_validate(orm_user))
            if orm_user
            else None
        )

    def search_artists(
        self, session: Session, query: str, limit: int, offset: int
    ) -> list[Artist]:
        statement = (
            select(ArtistORM)
            .outerjoin(ArtistAlias)
            .where(
                (col(ArtistORM.name).ilike(f"%{query}%"))
                | (col(ArtistAlias.name).ilike(f"%{query}%"))
            )
            .limit(limit)
            .offset(offset)
            .options(selectinload(in_load_typing(ArtistORM.albums)))
        )
        orm_artists = session.exec(statement).all()
        return [artist_from_orm(artist) for artist in orm_artists]

    def search_albums(
        self, session: Session, query: str, limit: int, offset: int
    ) -> list[Album]:
        statement = (
            select(AlbumORM)
            .where(col(AlbumORM.title).ilike(f"%{query}%"))
            .limit(limit)
            .offset(offset)
            .options(
                selectinload(in_load_typing(AlbumORM.tracks_links))
                .selectinload(in_load_typing(TrackAlbumLink.track))
                .selectinload(in_load_typing(TrackORM.files)),
                selectinload(in_load_typing(AlbumORM.tracks_links))
                .selectinload(in_load_typing(TrackAlbumLink.track))
                .selectinload(in_load_typing(TrackORM.albums_links)),
                selectinload(in_load_typing(AlbumORM.artists)),
            )
        )
        orm_albums = session.exec(statement).all()
        return [album_from_orm(album) for album in orm_albums]

    def search_tracks(
        self, session: Session, query: str, limit: int, offset: int
    ) -> list[Track]:
        statement = (
            select(TrackORM)
            .where(col(TrackORM.title).ilike(f"%{query}%"))
            .limit(limit)
            .offset(offset)
            .options(
                selectinload(in_load_typing(TrackORM.files)),
                selectinload(in_load_typing(TrackORM.albums_links))
                .selectinload(in_load_typing(TrackAlbumLink.album))
                .selectinload(in_load_typing(AlbumORM.artists)),
            )
        )
        orm_tracks = session.exec(statement).all()
        return [track_from_orm(track) for track in orm_tracks]

    def search_playlists(
        self, session: Session, query: str, limit: int, offset: int
    ) -> list[Playlist]:
        orm_playlists = session.exec(
            select(PlaylistORM)
            .where(col(PlaylistORM.title).ilike(f"%{query}%"))
            .limit(limit)
            .offset(offset)
        ).all()
        return [playlist_from_orm(playlist) for playlist in orm_playlists]

    def get_all_user_starred(
        self, session: Session, user_id: int
    ) -> tuple[list[Track], list[Album], list[Artist]] | None:
        user = session.exec(select(UserORM).where(UserORM.id == user_id)).first()
        if user is None:
            return None
        starred_tracks = [track_from_orm(track) for track in user.starred_tracks]
        starred_albums = [album_from_orm(album) for album in user.starred_albums]
        starred_artists = [artist_from_orm(artist) for artist in user.starred_artists]

        return (starred_tracks, starred_albums, starred_artists)

    def get_user_playlists(
        self, session: Session, user_id: int, size: int, offset: int
    ) -> list[Playlist]:
        statement = (
            (
                select(PlaylistORM)
                .join(col(PlaylistORM.owners))
                .where(UserORM.id == user_id)
                .options(
                    selectinload(cast(InstrumentedAttribute[Any], PlaylistORM.owners)),
                    selectinload(
                        cast(InstrumentedAttribute[Any], PlaylistORM.track_links)
                    ),
                )
            )
            .limit(size)
            .offset(offset)
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

    def delete_user_by_id(self, session: Session, user_id: int) -> int:
        stm = delete(UserORM).where(col(UserORM.id) == user_id)
        result = session.exec(stm)
        session.commit()
        return result.rowcount

    def delete_user_by_username(self, session: Session, username: str) -> int:
        stm = delete(UserORM).where(col(UserORM.username) == username)
        result = session.exec(stm)
        session.commit()
        return result.rowcount

    def bulk_delete_by_links(
        self, session: Session, provider_link: list[tuple[str, str]]
    ) -> tuple[int, int, int, int]:
        select_ids = select(
            ObjectStorageORM.id,
            ObjectStorageORM.audio_id,
            ObjectStorageORM.lyrics_id,
            ObjectStorageORM.music_video_id,
        ).where(
            tuple_(col(ObjectStorageORM.link_provider), col(ObjectStorageORM.link)).in_(
                provider_link
            )
        )
        ids_statement = session.exec(select_ids).all()
        links_ids = [r[0] for r in ids_statement]
        audio_ids = [r[1] for r in ids_statement]
        lyrics_ids = [r[2] for r in ids_statement]
        videos_ids = [r[3] for r in ids_statement]
        covers_links_count = (
            session.exec(
                select(func.count(ObjectStorageORM.id)).where(
                    col(ObjectStorageORM.id).in_(links_ids),
                    col(ObjectStorageORM.audio_id).is_(None),
                    col(ObjectStorageORM.lyrics_id).is_(None),
                    col(ObjectStorageORM.music_video_id).is_(None),
                )
            ).one()
            or 0
        )
        session.exec(
            delete(ObjectStorageORM).where(col(ObjectStorageORM.id).in_(links_ids))
        )
        session.flush()
        audio_statement = select(AudioFileORM).where(
            col(AudioFileORM.id).in_(audio_ids)
        )
        searched_audios = session.exec(audio_statement).all()
        audios_for_deleting = []
        for audio in searched_audios:
            if len(audio.links) == 0:
                audios_for_deleting.append(audio.id)
        deleted_audio = session.exec(
            delete(AudioFileORM).where(col(AudioFileORM.id).in_(audios_for_deleting))
        )

        searched_lyrics = session.exec(
            select(LyricsORM).where(col(LyricsORM.id).in_(lyrics_ids))
        ).all()
        lyrics_for_deleting = []
        for lyrics in searched_lyrics:
            if len(lyrics.path) == 0:
                lyrics_for_deleting.append(lyrics.id)
        deleted_lyrics = session.exec(
            delete(LyricsORM).where(col(LyricsORM.id).in_(lyrics_for_deleting))
        )

        searched_videos = session.exec(
            select(MusicVideoORM).where(col(MusicVideoORM.id).in_(videos_ids))
        ).all()
        videos_for_deleting = []
        for video in searched_videos:
            if len(video.local_link) == 0:
                videos_for_deleting.append(video.id)
        deleted_videos = session.exec(
            delete(MusicVideoORM).where(col(MusicVideoORM.id).in_(videos_for_deleting))
        )

        session.commit()
        return (
            deleted_audio.rowcount,
            covers_links_count,
            deleted_lyrics.rowcount,
            deleted_videos.rowcount,
        )

    def get_all_tracks(self, session: Session) -> list[Track]:
        statement = select(TrackORM).options(
            selectinload(in_load_typing(TrackORM.files))
        )
        orm_tracks = session.exec(statement).all()
        return [track_from_orm(track) for track in orm_tracks]

    def get_all_artists(
        self, session: Session, size: int | None, offset: int | None
    ) -> list[Artist]:
        statement = select(ArtistORM).options(
            selectinload(in_load_typing(ArtistORM.albums))
        )
        if size:
            statement = statement.limit(size)
        if offset:
            statement = statement.offset(offset)
        orm_artists = session.exec(statement).all()
        return [artist_from_orm(artist) for artist in orm_artists]

    def get_all_albums(self, session: Session, size: int, offset: int) -> list[Album]:
        statement = (
            select(AlbumORM)
            .options(
                selectinload(in_load_typing(AlbumORM.tracks_links))
                .selectinload(in_load_typing(TrackAlbumLink.track))
                .selectinload(in_load_typing(TrackORM.files)),
                selectinload(in_load_typing(AlbumORM.tracks_links))
                .selectinload(in_load_typing(TrackAlbumLink.track))
                .selectinload(in_load_typing(TrackORM.albums_links)),
                selectinload(in_load_typing(AlbumORM.artists)),
            )
            .limit(size)
            .offset(offset)
        )
        orm_albums = session.exec(statement).all()
        return [album_from_orm(album) for album in orm_albums]

    def get_all_tracks_storage_links(self, session: Session) -> set[tuple[str, str]]:
        combined = (
            ObjectStorageORM.link_provider + literal("///") + ObjectStorageORM.link
        ).label("combined")
        statement = select(combined, ObjectStorageORM.file_name).where(
            ObjectStorageORM.link_type == "storage"
        )
        result = session.exec(statement).all()
        return set(result)

    def get_track_by_id(self, session: Session, id: int) -> Track | BaseError:
        statement = (
            select(TrackORM)
            .where(TrackORM.id == id)
            .options(
                selectinload(in_load_typing(TrackORM.files)),
                selectinload(in_load_typing(TrackORM.artists)),
                selectinload(in_load_typing(TrackORM.lyrics)),
                selectinload(in_load_typing(TrackORM.music_videos)),
                selectinload(in_load_typing(TrackORM.albums_links)).selectinload(
                    in_load_typing(TrackAlbumLink.album)
                ),
            )
        )
        orm_track = session.exec(statement).first()
        return track_from_orm(orm_track) if orm_track else NotFoundError()

    def get_albums_cursor(
        self, session: Session, limit: int, cursor: str | None
    ) -> tuple[list[Album], str | None]:
        last_id, created_at = decode_cursor(cursor) if cursor else (None, None)
        statement = (
            select(AlbumORM)
            .order_by(col(AlbumORM.created_at).desc(), col(AlbumORM.id).desc())
            .limit(limit + 1)
        )
        if last_id is not None and created_at is not None:
            statement = statement.where(
                or_(
                    col(AlbumORM.created_at) < created_at,
                    and_(
                        col(AlbumORM.created_at) == created_at,
                        col(AlbumORM.id) < last_id,
                    ),
                )
            )
        albums = list(session.exec(statement).all())
        next_cursor = None
        if len(albums) > limit:
            albums.pop()
            last_item = albums[-1]
            next_cursor = encode_cursor(last_item.id, last_item.created_at)
        return [album_from_orm(album) for album in albums], next_cursor

    def get_artist_cursor(
        self, session: Session, limit: int, cursor: str | None
    ) -> tuple[list[Artist], str | None]:
        last_id, created_at = decode_cursor(cursor) if cursor else (None, None)
        statement = (
            select(ArtistORM)
            .order_by(col(ArtistORM.created_at).desc(), col(ArtistORM.id).desc())
            .limit(limit + 1)
        )
        if last_id is not None and created_at is not None:
            statement = statement.where(
                or_(
                    col(ArtistORM.created_at) < created_at,
                    and_(
                        col(ArtistORM.created_at) == created_at,
                        col(ArtistORM.id) < last_id,
                    ),
                )
            )
        artists = list(session.exec(statement).all())
        next_cursor = None
        if len(artists) > limit:
            artists.pop()
            last_item = artists[-1]
            next_cursor = encode_cursor(last_item.id, last_item.created_at)
        return [artist_from_orm(artist) for artist in artists], next_cursor

    def get_track_cursor(
        self, session: Session, limit: int, cursor: str | None
    ) -> tuple[list[Track], str | None]:
        last_id, created_at = decode_cursor(cursor) if cursor else (None, None)
        statement = (
            select(TrackORM)
            .order_by(col(TrackORM.created_at).desc(), col(TrackORM.id).desc())
            .limit(limit + 1)
        )
        if last_id is not None and created_at is not None:
            statement = statement.where(
                or_(
                    col(TrackORM.created_at) < created_at,
                    and_(
                        col(TrackORM.created_at) == created_at,
                        col(TrackORM.id) < last_id,
                    ),
                )
            )
        tracks = list(session.exec(statement).all())
        next_cursor = None
        if len(tracks) > limit:
            tracks.pop()
            last_item = tracks[-1]
            next_cursor = encode_cursor(last_item.id, last_item.created_at)
        return [track_from_orm(track) for track in tracks], next_cursor

    def get_album_by_id(self, session: Session, id: int) -> Album | None:
        statement = (
            select(AlbumORM)
            .where(AlbumORM.id == id)
            .options(
                selectinload(in_load_typing(AlbumORM.tracks_links))
                .selectinload(in_load_typing(TrackAlbumLink.track))
                .selectinload(in_load_typing(TrackORM.files)),
                selectinload(in_load_typing(AlbumORM.tracks_links))
                .selectinload(in_load_typing(TrackAlbumLink.track))
                .selectinload(in_load_typing(TrackORM.albums_links)),
                selectinload(in_load_typing(AlbumORM.artists)),
            )
        )
        orm_album = session.exec(statement).first()
        return album_from_orm(orm_album) if orm_album else None

    def get_album_orm_by_id(self, session: Session, id: int) -> AlbumORM | None:
        return session.get(AlbumORM, id)

    def get_album_orm_by_title(self, session: Session, title: str) -> AlbumORM | None:
        return session.exec(select(AlbumORM).where(AlbumORM.title == title)).first()

    def get_artist_orm_by_id(self, session: Session, id: int) -> ArtistORM | None:
        return session.get(ArtistORM, id)

    def get_artist_orm_by_name(self, session: Session, name: str) -> ArtistORM | None:
        return session.exec(select(ArtistORM).where(ArtistORM.name == name)).first()

    def get_playlist_orm_by_id(self, session: Session, id: int) -> PlaylistORM | None:
        return session.get(PlaylistORM, id)

    def delete_orphans(self, session: Session) -> tuple[int, int, int]:
        deleted_tracks = session.exec(
            delete(TrackORM).where(
                col(TrackORM.id).not_in(
                    select(AudioFileORM.track_id).where(
                        col(AudioFileORM.track_id).is_not(None)
                    )
                )
            )
        )
        session.flush()

        deleted_albums = session.exec(
            delete(AlbumORM).where(
                col(AlbumORM.id).not_in(select(TrackAlbumLink.album_id))
            )
        )
        session.flush()

        deleted_artists = session.exec(
            delete(ArtistORM).where(
                col(ArtistORM.id).not_in(select(AlbumArtistLink.artist_id)),
                col(ArtistORM.id).not_in(select(TrackArtistsLink.artist_id)),
                col(ArtistORM.id).not_in(
                    select(AlbumArtistLink.artist_id).where(
                        col(AlbumArtistLink.album_id).is_not(None)
                    )
                ),
                col(ArtistORM.id).not_in(
                    select(TrackArtistsLink.artist_id).where(
                        col(TrackArtistsLink.track_id).is_not(None)
                    )
                ),
            )
        )
        session.flush()

        return (
            deleted_tracks.rowcount,
            deleted_albums.rowcount,
            deleted_artists.rowcount,
        )

    def get_artist_by_id(self, session: Session, id: int) -> Artist | None:
        statement = (
            select(ArtistORM)
            .where(ArtistORM.id == id)
            .options(
                selectinload(in_load_typing(ArtistORM.albums)).selectinload(
                    in_load_typing(AlbumORM.tracks_links)
                ),
                selectinload(in_load_typing(ArtistORM.albums)).selectinload(
                    in_load_typing(AlbumORM.artists)
                ),
            )
        )
        orm_artist = session.exec(statement).first()
        return artist_from_orm(orm_artist) if orm_artist else None

    def get_model_count(self, session: Session, model) -> int:
        model_count = session.scalar(select(func.count(model.id))) or 0
        return model_count

    def get_genre_counts(self, session: Session) -> tuple[int, int, int, int]:
        genre_count: int = session.scalar(select(func.count(GenreORM.id))) or 0
        tracks_genre: int = (
            session.scalar(select(func.count(distinct(col(TrackGenreLink.track_id)))))
            or 0
        )
        albums_genre: int = (
            session.scalar(select(func.count(distinct(col(AlbumGenreLink.album_id)))))
            or 0
        )
        artists_genre: int = (
            session.scalar(select(func.count(distinct(col(ArtistGenreLink.artist_id)))))
            or 0
        )
        return (genre_count, tracks_genre, albums_genre, artists_genre)

    def get_moods_counts(self, session: Session) -> tuple[int, int]:
        mood_count: int = session.scalar(select(func.count(MoodORM.id))) or 0
        tracks_moods: int = (
            session.scalar(select(func.count(distinct(col(TrackMoodLink.track_id)))))
            or 0
        )

        return (mood_count, tracks_moods)

    def get_count_with_lyrics(self, session: Session) -> int:
        tracks_count: int = (
            session.scalar(
                select(func.count(TrackORM.id)).where(col(TrackORM.lyrics).any())
            )
            or 0
        )
        return tracks_count

    def get_count_with_videos(self, session: Session) -> int:
        tracks_count: int = (
            session.scalar(
                select(func.count(TrackORM.id)).where(col(TrackORM.music_videos).any())
            )
            or 0
        )
        return tracks_count

    def get_count_with_cover(self, session: Session, model) -> int:
        model_count = (
            session.scalar(
                select(func.count(model.id)).where(model.cover_path.is_not(None))
            )
            or 0
        )
        return model_count

    def find_track(
        self,
        session: Session,
        title: str,
        album_title: str | None = None,
        artists: list[str] | None = None,
    ) -> Track | None:
        normalized_title = title.strip().lower()
        stmt = select(TrackORM).where(TrackORM.normalized_title == normalized_title)
        if album_title:
            normalized_album = album_title.strip().lower()
            stmt.join(col(TrackORM.albums_links)).where(
                TrackAlbumLink.album.normalized_title == normalized_album
            ).distinct()
        if artists:
            normalized_names = [name.strip().lower() for name in artists]
            stmt.join(col(TrackORM.artists)).where(
                col(ArtistORM.normalized_name).in_(normalized_names)
            ).distinct()
        track = session.exec(stmt).first()
        return track_from_orm(track) if track else None

    def get_artists_by_name(
        self, session: Session, artists: list[str], count: int
    ) -> list[Artist]:
        normalized_names = [artist.strip().lower() for artist in artists]
        db_artists = session.exec(
            select(ArtistORM)
            .where(col(ArtistORM.normalized_name).in_(normalized_names))
            .limit(count)
        ).all()
        return [artist_from_orm(artist) for artist in db_artists]

    def get_artists_random_tracks(
        self, session: Session, artists: list[str], count: int
    ) -> list[Track]:
        normalized_names = [name.strip().lower() for name in artists]
        stmt = (
            select(TrackORM)
            .join(col(TrackORM.artists))
            .where(col(ArtistORM.normalized_name).in_(normalized_names))
            .order_by(func.random())
            .limit(count)
        )
        tracks = session.exec(stmt).all()
        return [track_from_orm(track) for track in tracks]
