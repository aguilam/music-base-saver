import time
from core.services import (
    album_service,
    artist_service,
    playlist_service,
    server_service,
    track_service,
    user_service,
)


class ScrobblersManager:
    def __init__(self):
        self.scrobblers, self.start_errors.scrobblers = load_modules(
            self.config.get("scrobbler", {}), import_modules("scrobbler", BaseScrobbler)
        )

    def scrobble(
        self, id: int, user_id: int, listen_time: int | None = None
    ) -> BaseError | None:
        with self.db_manager.get_session() as session:
            track = self.db_manager.get_track_by_id(session, id)
            if isinstance(track, BaseError):
                return track
            if listen_time is None:
                listen_time = int(time.time())
            for scrobbler in self.scrobblers:
                provider_key = self.db_manager.get_provider_key(
                    session, scrobbler.tag, user_id
                )
                if provider_key is None:
                    continue
                scrobbler_class = scrobbler.instance
                scrobbler_class.submit_listen(track, provider_key.key, listen_time)

    def post_now_playing(self, id: int, user_id: int) -> BaseError | None:
        with self.db_manager.get_session() as session:
            track = self.db_manager.get_track_by_id(session, id)
            if isinstance(track, BaseError):
                return track
            for scrobbler in self.scrobblers:
                provider_key = self.db_manager.get_provider_key(
                    session, scrobbler.tag, user_id
                )
                if provider_key is None:
                    continue
                scrobbler_class = scrobbler.instance
                scrobbler_class.post_playing_now(track, provider_key.key)

    def get_similiar_artists(self, id: int, count: int = 5) -> list[Artist] | BaseError:
        with self.db_manager.get_session() as session:
            artist = self.db_manager.get_artist_by_id(session, id)
            if artist is None:
                return NotFoundError()
            artists = self.scrobblers[0].instance.get_similiar_artists(artist)
            db_artists = self.db_manager.get_artists_by_name(session, artists, count)
            return db_artists

    def get_similiar_artists_random_tracks(
        self, artist_id: int, count: int
    ) -> list[Track] | BaseError:
        with self.db_manager.get_session() as session:
            artist = self.db_manager.get_artist_by_id(session, artist_id)
            if artist is None:
                return NotFoundError()
            artists = self.scrobblers[0].instance.get_similiar_artists(artist)
            tracks = self.db_manager.get_artists_random_tracks(session, artists, count)
            return tracks

    def get_user_tracks_recommendations(
        self, user_id: int, count: int
    ) -> list[Track] | BaseError:
        with self.db_manager.get_session() as session:
            scrobbler = self.scrobblers[0]
            provider_key = self.db_manager.get_provider_key(
                session, scrobbler.tag, user_id
            )
            if provider_key is None:
                return NotFoundError()
            tracks = scrobbler.instance.get_tracks_recommendations(
                provider_key.key, count
            )
            db_tracks: list[Track] = []
            for track in tracks:
                album_name = next((album.title for album in track.albums), None)
                artists_names = [artist.name for artist in track.artists]
                db_track = self.db_manager.find_track(
                    session, track.title, album_name, artists_names
                )
                if db_track is not None:
                    db_tracks.append(db_track)
            return db_tracks
