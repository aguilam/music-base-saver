from core.db.manager import DBManager
from core.modules.scrobblers.loader import load_scrobblers
from core.errors import BaseError, NotFoundError
from core.schemas import TrackShort, ArtistShort, Track
import time
from core.services import (
    artist_service,
    track_service,
    user_service,
)


class _ScrobblersManager:
    def __init__(self):
        self.config = dict()
        self.scrobblers, _ = load_scrobblers(self.config)

    def scrobble(
        self, id: int, user_id: int, listen_time: int | None = None
    ) -> BaseError | None:
        with DBManager.get_session() as session:
            track = track_service.get_track_by_id(session, id)
            if isinstance(track, BaseError):
                return track
            if listen_time is None:
                listen_time = int(time.time())
            for scrobbler in self.scrobblers:
                provider_key = user_service.get_provider_key(
                    session, scrobbler.tag, user_id
                )
                if provider_key is None:
                    continue
                scrobbler_class = scrobbler.instance
                scrobbler_class.submit_listen(track, provider_key.key, listen_time)

    def post_now_playing(self, id: int, user_id: int) -> BaseError | None:
        with DBManager.get_session() as session:
            track = track_service.get_track_by_id(session, id)
            if isinstance(track, BaseError):
                return track
            for scrobbler in self.scrobblers:
                provider_key = user_service.get_provider_key(
                    session, scrobbler.tag, user_id
                )
                if provider_key is None:
                    continue
                scrobbler_class = scrobbler.instance
                scrobbler_class.post_playing_now(track, provider_key.key)

    def get_similiar_artists(
        self, id: int, count: int = 5
    ) -> list[ArtistShort] | BaseError:
        with DBManager.get_session() as session:
            artist = artist_service.get_artist_by_id(session, id)
            if isinstance(artist, BaseError):
                return artist
            artists = self.scrobblers[0].instance.get_similiar_artists(artist)
            db_artists = artist_service.get_artists_by_name(session, artists, count)
            return db_artists

    def get_similiar_artists_random_tracks(
        self, artist_id: int, count: int
    ) -> list[TrackShort] | BaseError:
        with DBManager.get_session() as session:
            artist = artist_service.get_artist_by_id(session, artist_id)
            if isinstance(artist, BaseError):
                return artist
            artists = self.scrobblers[0].instance.get_similiar_artists(artist)
            tracks = artist_service.get_artists_random_tracks(session, artists, count)
            return tracks

    def get_user_tracks_recommendations(
        self, user_id: int, count: int
    ) -> list[TrackShort] | BaseError:
        with DBManager.get_session() as session:
            scrobbler = self.scrobblers[0]
            provider_key = user_service.get_provider_key(
                session, scrobbler.tag, user_id
            )
            if provider_key is None:
                return NotFoundError()
            tracks = scrobbler.instance.get_tracks_recommendations(
                provider_key.key, count
            )
            db_tracks: list[Track] = []
            # TODO: Rewrite find track to TrackShort and get by albums
            for track in tracks:
                album_name = next((album.title for album in track.albums), None)
                artists_names = [artist.name for artist in track.artists]
                db_track = track_service.find_track(
                    session, track.title, album_name, artists_names
                )
                if not isinstance(db_track, BaseError):
                    db_tracks.append(db_track)
            return db_tracks


ScrobblersManager = _ScrobblersManager()
