from sqlmodel import Session, select

from core.db.models import (
    AlbumArtistLink,
    AudioFileORM,
    GenreORM,
    ObjectStorageORM,
    TrackAlbumLink,
    TrackArtistsLink,
    TrackGenreLink,
    TrackMoodLink,
    TrackORM,
)
from core.errors import BaseError
from core.responses import LyricsResponse
from core.schemas import FilePathInfo, MusicVideo, Track, TrackMetadata, TrackShort
from core.services.album_service import album_repository
from core.services.artist_service import artist_repository
from core.services.track_service import track_repository


def get_track_by_id(session: Session, id: int) -> Track | BaseError:
    return track_repository.get_track_by_id(session, id)


def find_or_create_genre(session: Session, genre_name: str) -> GenreORM:
    return track_repository.find_or_create_genre(session, genre_name)


def get_track_by_title(session: Session, title: str) -> Track | BaseError:
    return track_repository.get_track_by_title(session, title)


def get_video_by_id(session: Session, video_id: int) -> MusicVideo | BaseError:
    return track_repository.get_video_by_id(session, video_id)


def get_all_tracks(session: Session) -> list[TrackShort]:
    return track_repository.get_all_tracks(session)


def find_track(
    session: Session,
    title: str,
    album_title: str | None = None,
    artists: list[str] | None = None,
) -> Track | BaseError:
    return track_repository.find_track(session, title, album_title, artists)


def get_all_tracks_storage_links(session: Session) -> set[tuple[str, str]]:
    return track_repository.get_all_tracks_storage_links(session)


def get_tracks_cursor(
    session: Session, cursor: str | None, limit: int = 20
) -> tuple[list[TrackShort], str | None]:
    return track_repository.get_track_cursor(session, limit, cursor)


def get_lyrics(session: Session, track_id: int) -> list[LyricsResponse] | BaseError:
    track = track_repository.get_track_by_id(session, track_id)
    if isinstance(track, BaseError):
        return track
    artists_name = ", ".join([artist.name for artist in track.artists])
    lyrics_list: list[LyricsResponse] = []
    for lyrics in track.lyrics:
        lyrics_list.append(
            LyricsResponse(
                artist=artists_name,
                title=track.title,
                id=lyrics.id,
                is_synced=lyrics.is_synced,
                synced_text=lyrics.synced_text,
                plain_text=lyrics.plain_text,
                language=lyrics.language,
                offset=lyrics.offset,
            )
        )
    return lyrics_list


def get_genres(session: Session) -> list[dict[str, str | int]]:
    genres = track_repository.get_genres(session)
    counted_genres = []
    for genre in genres:
        counted_genres.append(
            {
                "name": genre.name,
                "track_count": len(genre.tracks),
                "album_count": len(genre.albums),
            }
        )
    return counted_genres


def get_moods(session: Session) -> list[dict[str, str | int]]:
    moods = track_repository.get_moods(session)
    counted_moods = []
    for mood in moods:
        counted_moods.append(
            {
                "name": mood.name,
                "track_count": len(mood.tracks),
            }
        )
    return counted_moods


def search_tracks(
    session: Session, query: str, limit: int, offset: int
) -> list[TrackShort]:
    return track_repository.search_tracks(session, query, limit, offset)


def add_new_track(
    session: Session,
    track_metadata: TrackMetadata,
    track_info: FilePathInfo,
    storage_id: str,
    cover_id: int | None = None,
) -> int:
    db_album = None
    track_artists = [
        artist_repository.find_or_create_artist(session, artist)
        for artist in track_metadata.artists
    ]
    new_track = TrackORM(
        title=track_metadata.title,
        normalized_title=track_metadata.title.strip().lower(),
        length=track_metadata.length,
        bpm=track_metadata.bpm,
        year=track_metadata.year,
    )
    session.add(new_track)
    session.flush()
    for album in track_metadata.albums:
        db_album = album_repository.find_or_create_album(
            session, album.title, album.album_artists
        )
        if db_album.cover_path is None and cover_id:
            db_album.cover_path = cover_id
        session.add(db_album)
        session.flush()
        db_album_artists = [
            artist_repository.find_or_create_artist(session, artist)
            for artist in album.album_artists
        ]
        for artist in db_album_artists:
            exists = session.exec(
                select(AlbumArtistLink).where(
                    AlbumArtistLink.artist_id == artist.id,
                    AlbumArtistLink.album_id == db_album.id,
                )
            ).first()
            if not exists:
                session.add(AlbumArtistLink(artist_id=artist.id, album_id=db_album.id))
            session.flush()
        track_album = TrackAlbumLink(
            track_id=new_track.id,
            album_id=db_album.id,
            album_position=album.album_position,
            disc_number=album.disc_number,
        )
        session.add(track_album)
        session.flush()
    for genre in track_metadata.genres:
        track_genre = track_repository.find_or_create_genre(session, genre)
        track_genre_link = TrackGenreLink(
            track_id=new_track.id, genre_id=track_genre.id
        )
        session.add(track_genre_link)
        session.flush()
    for mood in track_metadata.moods:
        track_mood = track_repository.find_or_create_mood(session, mood)
        track_mood_link = TrackMoodLink(track_id=new_track.id, mood_id=track_mood.id)
        session.add(track_mood_link)
        session.flush()
    audio_file = AudioFileORM(
        track_id=new_track.id, bitrate=track_metadata.bitrate, is_primary=True
    )
    new_track.files.append(audio_file)
    session.add(audio_file)
    session.flush()
    new_link = ObjectStorageORM(
        audio_id=audio_file.id,
        file_name=track_info.filename,
        link_provider=storage_id,
        link=track_info.link,
    )
    session.add(new_link)
    for artist in track_artists:
        track_artist = TrackArtistsLink(artist_id=artist.id, track_id=new_track.id)
        session.add(track_artist)
    session.flush()
    return new_track.id


# def delete_track(session: Session, track_id: int):
#    with track_repository.get_session() as session:
#        track = track_repository.delete_track(session, track_id)
#        return track
