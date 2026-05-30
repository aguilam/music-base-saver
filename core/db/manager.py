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

from sqlalchemy import tuple_, or_, func
from core.db.mappers import (
    artist_from_orm,
    album_from_orm,
    playlist_from_orm,
    track_from_orm,
    music_video_from_orm,
    user_from_orm,
    object_storage_from_orm,
    mood_from_orm,
    genre_from_orm,
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
    ProviderKeyORM,
    PlaylistTrackLink,
    AudioFileORM,
    TrackAlbumLink,
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

    def get_tracks_by_artist_name(self, session: Session, artist_name: str):
        tracks = session.exec(
            select(TrackORM).join(TrackORM.artists).where(ArtistORM.name == artist_name)
        ).all()
        return [track_from_orm(track) for track in tracks]

    def get_provider_key(self, session: Session, provider: str, user_id: int):
        statement = select(ProviderKeyORM.key).where(
            ProviderKeyORM.provider == provider, ProviderKeyORM.user_id == user_id
        )
        key = session.exec(statement).first()
        return key

    def get_api_key(self, session: Session, user_id: int):
        statement = select(ApiKeyORM.key).where(ApiKeyORM.user_id == user_id)
        keys = session.exec(statement).all()
        return keys

    def get_moods(self, session: Session):
        moods = (
            session.execute(select(MoodORM).options(selectinload(MoodORM.tracks)))
            .scalars()
            .all()
        )
        return [mood_from_orm(mood) for mood in moods]

    def get_genres(self, session: Session):
        genres = (
            session.execute(select(GenreORM).options(selectinload(GenreORM.tracks)))
            .scalars()
            .all()
        )
        return [genre_from_orm(genre) for genre in genres]

    def get_storage_object_by_id(self, session: Session, id: int):
        storage = session.exec(
            select(ObjectStorageORM).where(ObjectStorageORM.id == id)
        ).first()

        return object_storage_from_orm(storage) if storage else None

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

    def find_or_create_artist(self, session: Session, name: str):
        normalized_name = name.lower().strip()

        existed_artist = session.exec(
            select(ArtistORM).where(
                or_(
                    func.lower(ArtistORM.name) == normalized_name,
                    ArtistORM.aliases.any(
                        func.lower(ArtistAlias.name) == normalized_name
                    ),
                )
            )
        ).first()
        if existed_artist:
            return existed_artist
        new_artist = ArtistORM(name=name)
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
    ):
        normalized_title = title.lower().strip()
        stmt = select(AlbumORM).where(func.lower(AlbumORM.title) == normalized_title)
        if artists_names:
            stmt = (
                stmt.join(AlbumORM.artists)
                .where(ArtistORM.name.in_(artists_names))
                .distinct()
            )
        existed_album = session.exec(stmt).first()
        if existed_album:
            return existed_album
        new_album = AlbumORM(title=title, year=year, description=description, type=type)
        session.add(new_album)
        session.flush()
        return new_album

    def find_or_create_mood(self, session: Session, mood_name: str):
        normalized_name = mood_name.lower().strip()
        mood = session.exec(
            select(MoodORM).where(func.lower(MoodORM.name) == normalized_name)
        ).first()
        if mood:
            return mood
        new_mood = MoodORM(name=mood_name.strip())
        session.add(new_mood)
        session.flush()
        return new_mood

    def find_or_create_genre(self, session: Session, genre_name: str):
        normalized_name = genre_name.lower().strip()
        genre = session.exec(
            select(GenreORM).where(func.lower(GenreORM.name) == normalized_name)
        ).first()
        if genre:
            return genre
        new_genre = GenreORM(name=genre_name.strip())
        session.add(new_genre)
        session.flush()
        return new_genre

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
                selectinload(PlaylistORM.track_links)
                .selectinload(PlaylistTrackLink.track)
                .selectinload(TrackORM.files),
                selectinload(PlaylistORM.track_links)
                .selectinload(PlaylistTrackLink.track)
                .selectinload(TrackORM.album)
                .selectinload(AlbumORM.artist_rel),
            )
        )
        orm_playlist = session.exec(statement).first()
        return playlist_from_orm(orm_playlist) if orm_playlist else None

    def create_user(self, session: Session, username: str, email: str, password: str):
        new_user = UserORM(username=username, email=email, password=password)
        session.add(new_user)
        return user_from_orm(new_user)

    def update_user(
        self,
        session: Session,
        user_id: int,
        username: str | None,
        password: str | None,
        is_admin: bool | None,
    ):
        changed_user = session.exec(
            select(UserORM).where(UserORM.username == username)
        ).first()
        if changed_user is None:
            return None
        same_user = changed_user.id == user_id
        is_changing_admin = changed_user.is_admin
        if not same_user:
            user = session.exec(select(UserORM).where(UserORM.id == user_id)).first()
            if user and user.is_admin:
                is_changing_admin = True
            else:
                return None
        if is_admin is not None and is_changing_admin:
            changed_user.is_admin = is_admin
        if password and password is not changed_user.password:
            changed_user.password = password
        if username and username is not changed_user.username:
            changed_user.username = username
        return user_from_orm(changed_user)

    def delete_playlist(self, session: Session, id: int):
        statement = delete(PlaylistORM).where(PlaylistORM.id == id)
        session.exec(statement).first()

    def create_playlist(
        self,
        session: Session,
        user_id: int,
        name: str,
        cover_path: int | None,
        is_public: bool,
        tracks_id: list[int],
    ):
        user = session.exec(select(UserORM).where(UserORM.id == user_id)).first()
        if user is None:
            return None
        playlist = PlaylistORM(
            name=name, cover_path=cover_path, is_public=is_public, owner=user
        )
        session.add(playlist)
        session.flush()
        for position, track_id in enumerate(tracks_id, start=1):
            trackLink = PlaylistTrackLink(playlist.id, track_id, position=position)
            playlist.track_links.append(trackLink)
        return playlist_from_orm(playlist)

    def get_user_by_apikey(self, session: Session, api_key: str):
        orm_user = session.exec(
            select(UserORM).where(UserORM.api_key == api_key)
        ).first()
        return user_from_orm(orm_user) if orm_user else None

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
        user = session.exec(select(UserORM).where(UserORM.id == id)).first()
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

    def delete_user_by_id(self, session: Session, user_id: int):
        stm = delete(UserORM).where(UserORM.id == user_id)
        result = session.exec(stm)
        session.commit()
        return result.rowcount

    def delete_user_by_username(self, session: Session, username: str):
        stm = delete(UserORM).where(UserORM.username == username)
        result = session.exec(stm)
        session.commit()
        return result.rowcount

    def bulk_delete_by_links(
        self, session: Session, provider_link: list[tuple[str, str]]
    ):
        select_ids = select(ObjectStorageORM.id, ObjectStorageORM.audio_id).where(
            tuple_(ObjectStorageORM.link_provider, ObjectStorageORM.link).in_(
                provider_link
            )
        )
        ids_statement = session.exec(select_ids).all()
        links_ids = [r[0] for r in ids_statement]
        track_ids = [r[1] for r in ids_statement]
        delete_links_statement = delete(ObjectStorageORM).where(
            ObjectStorageORM.id.in_(links_ids)
        )
        session.exec(delete_links_statement)
        delete_tracks_statement = delete(TrackORM).where(TrackORM.id.in_(track_ids))
        tracks = session.exec(delete_tracks_statement)
        session.commit()
        return tracks.rowcount

    def get_all_tracks(self, session: Session):
        statement = select(TrackORM).options(selectinload(TrackORM.files))
        orm_tracks = session.exec(statement).all()
        return [track_from_orm(track) for track in orm_tracks]

    def get_all_artists(self, session: Session):
        statement = select(ArtistORM).options(selectinload(ArtistORM.albums))
        orm_artists = session.exec(statement).all()
        return [artist_from_orm(artist) for artist in orm_artists]

    def get_all_albums(self, session: Session):
        statement = select(AlbumORM).options(
            selectinload(AlbumORM.tracks).selectinload(TrackORM.files),
            selectinload(AlbumORM.tracks).selectinload(TrackORM.album),
            selectinload(AlbumORM.artist_rel),
        )
        orm_albums = session.exec(statement).all()
        return [album_from_orm(album) for album in orm_albums]

    def get_all_tracks_storage_links(self, session: Session):
        combined = (
            ObjectStorageORM.link_provider + literal("///") + ObjectStorageORM.link
        ).label("combined")
        statement = select(combined, ObjectStorageORM.file_name).where(
            ObjectStorageORM.link_type == "storage"
        )
        result = session.exec(statement).all()
        return set(result)

    def get_track_by_id(self, session: Session, id: int):
        statement = (
            select(TrackORM)
            .where(TrackORM.id == id)
            .options(
                selectinload(TrackORM.files),
                selectinload(TrackORM.artists),
                selectinload(TrackORM.lyrics),
                selectinload(TrackORM.music_videos),
                selectinload(TrackORM.albums_links).selectinload(TrackAlbumLink.album),
            )
        )
        orm_track = session.exec(statement).first()
        return track_from_orm(orm_track) if orm_track else None

    def get_album_by_id(self, session: Session, id: int):
        statement = (
            select(AlbumORM)
            .where(AlbumORM.id == id)
            .options(
                selectinload(AlbumORM.tracks).selectinload(TrackORM.files),
                selectinload(AlbumORM.tracks).selectinload(TrackORM.albumы),
                selectinload(AlbumORM.artist_rel),
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
