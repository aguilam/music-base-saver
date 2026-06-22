from core.db.models import (
    TrackORM,
    ArtistORM,
    AlbumORM,
    PlaylistORM,
    MusicVideoORM,
    LyricsORM,
    UserORM,
    ObjectStorageORM,
    TrackAlbumLink,
    MoodORM,
    GenreORM,
    ApiKeyORM,
    ProviderKeyORM,
)
from core.schemas.schemas import (
    TrackShort,
    Track,
    ArtistShort,
    Artist,
    AlbumShort,
    Album,
    Playlist,
    MusicVideo,
    Lyrics,
    User,
    Mood,
    Genre,
    ObjectStorage,
    TrackAlbum,
    ApiKey,
    ProviderKey,
)


def artist_from_orm(artist: ArtistORM) -> Artist:
    return Artist(
        id=artist.id,
        name=artist.name,
        cover_path=artist.cover_path,
        description=artist.description,
        albums=[album_from_orm(album) for album in artist.albums],
        genres=[genre.name for genre in artist.genres],
    )


def artist_short_from_orm(artist: ArtistORM) -> ArtistShort:
    return ArtistShort(
        id=artist.id,
        name=artist.name,
        description=artist.description,
        cover_path=artist.cover_path,
    )


def album_from_orm(album: AlbumORM) -> Album:
    return Album(
        id=album.id,
        title=album.title,
        cover_path=album.cover_path,
        duration=album.duration,
        description=album.description,
        tracks_count=album.track_count,
        genres=[genre.name for genre in album.genres],
        artists=[artist_short_from_orm(artist) for artist in album.artists],
        tracks=[track_from_orm(link.track) for link in album.tracks_links],
        created_at=album.created_at,
    )


def album_short_from_orm(album: AlbumORM) -> AlbumShort:
    return AlbumShort(
        id=album.id,
        title=album.title,
        cover_path=album.cover_path,
        duration=album.duration,
        description=album.description,
        tracks_count=album.track_count,
        genres=[genre.name for genre in album.genres],
        artists=[artist_short_from_orm(artist) for artist in album.artists],
        tracks=[track_short_from_orm(link.track) for link in album.tracks_links],
        created_at=album.created_at,
    )


def playlist_from_orm(playlist: PlaylistORM) -> Playlist:
    return Playlist(
        id=playlist.id,
        title=playlist.title,
        cover_path=playlist.cover_path,
        is_public=playlist.is_public,
        owners=[user_from_orm(owner) for owner in playlist.owners],
        duration=playlist.duration,
        tracks_count=playlist.track_count,
        tracks=[track_from_orm(link.track) for link in playlist.track_links],
        created_at=playlist.created_at,
    )


def track_album_from_orm(link: TrackAlbumLink) -> TrackAlbum:
    album = link.album
    return TrackAlbum(
        title=album.title,
        duration=album.duration,
        tracks_count=album.track_count,
        artists=[artist_short_from_orm(artist) for artist in album.artists],
        id=album.id,
        cover_path=album.cover_path,
        created_at=album.created_at,
        disc_number=link.disc_number,
        album_position=link.album_position,
        is_primary=link.is_primary_album,
    )


def track_from_orm(track: TrackORM) -> Track:
    primary_file = next(
        (file for file in track.files if file.is_primary), track.files[0]
    )
    primary_album = next(
        (link.album for link in track.albums_links if link.is_primary_album), None
    )
    return Track(
        id=track.id,
        title=track.title,
        length=track.length,
        artists=[artist_short_from_orm(artist) for artist in track.artists],
        albums=[track_album_from_orm(link) for link in track.albums_links],
        cover_path=primary_album.cover_path if primary_album else None,
        path=(next((link.id for link in primary_file.links), None)),
        bpm=track.bpm,
        track_gain=primary_file.trackGain if primary_file else None,
        track_peak=primary_file.trackPeak if primary_file else None,
        year=track.year,
        lyrics=[lyrics_from_orm(lyrics) for lyrics in track.lyrics],
        music_videos=[music_video_from_orm(video) for video in track.music_videos],
        created_at=track.created_at,
    )


def track_short_from_orm(track: TrackORM) -> TrackShort:
    primary_file = next((file for file in track.files if file.is_primary), None)
    return TrackShort(
        id=track.id,
        title=track.title,
        length=track.length,
        cover_path=track.albums_links[0].album.cover_path,
        path=(
            next((link.id for link in primary_file.links), None)
            if primary_file
            else None
        ),
        bpm=track.bpm,
        track_gain=primary_file.trackGain if primary_file else None,
        track_peak=primary_file.trackPeak if primary_file else None,
        year=track.year,
        created_at=track.created_at,
    )


def mood_from_orm(mood: MoodORM) -> Mood:
    return Mood(
        id=mood.id,
        name=mood.name,
        tracks=[track_short_from_orm(track) for track in mood.tracks],
    )


def genre_from_orm(genre: GenreORM) -> Genre:
    return Genre(
        id=genre.id,
        name=genre.name,
        artists=[artist_short_from_orm(artist) for artist in genre.artists],
        albums=[album_short_from_orm(album) for album in genre.albums],
        tracks=[track_short_from_orm(track) for track in genre.tracks],
    )


def lyrics_from_orm(lyrics: LyricsORM) -> Lyrics:
    return Lyrics(
        id=lyrics.id,
        is_synced=lyrics.is_synced,
        synced_text=lyrics.synced_text,
        plain_text=lyrics.plain_text,
        language=lyrics.language,
        path=next((path.id for path in lyrics.path)),
        type=lyrics.type,
        offset=lyrics.offset,
        track_id=lyrics.track_id,
    )


def music_video_from_orm(music_video: MusicVideoORM) -> MusicVideo:
    return MusicVideo(
        id=music_video.id,
        local_link=next((link.id for link in music_video.local_link), None),
        track_id=music_video.track_id,
        duration_ms=music_video.duration_ms,
    )


def user_from_orm(user: UserORM) -> User:
    return User(
        id=user.id,
        username=user.username,
        password=user.password,
        email=user.email,
        is_admin=user.is_admin,
    )


def object_storage_from_orm(storage: ObjectStorageORM) -> ObjectStorage:
    return ObjectStorage(
        link_type=storage.link_type,
        link_provider=storage.link_provider,
        link=storage.link,
        id=storage.id,
        created_at=storage.created_at,
        track_id=storage.audio_id,
        music_video_id=storage.music_video_id,
        lyrics_id=storage.lyrics_id,
    )


def api_key_from_orm(api_key: ApiKeyORM) -> ApiKey:
    return ApiKey(
        id=api_key.id,
        key=api_key.key,
        user_id=api_key.user_id,
        revoked=api_key.revoked,
        created_at=api_key.created_at,
    )


def provider_key_from_orm(api_key: ProviderKeyORM) -> ProviderKey:
    return ProviderKey(
        id=api_key.id,
        provider=api_key.provider,
        key=api_key.key,
        user_id=api_key.user_id,
        created_at=api_key.created_at,
    )
