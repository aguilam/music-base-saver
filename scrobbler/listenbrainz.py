from scrobbler.base import Scrobbler
from core.schemas.schemas import HealthStatus, Track
import liblistenbrainz


class ListenBrainz(Scrobbler):
    TAG = "LBZ"

    def __init__(self, config):
        self.config = config

    def post_playing_now(self, track: Track, token: str):
        client = liblistenbrainz.ListenBrainz()
        client.set_auth_token(token)
        artists_names = [artist.name for artist in track.artists]
        artists = ", ".join(artists_names)
        listen = liblistenbrainz.Listen(track_name=track.title, artist_name=artists)
        client.submit_playing_now(listen)

    def submit_listen(self, track: Track, token: str, time: int | None):
        client = liblistenbrainz.ListenBrainz()
        client.set_auth_token(token)
        artists_names = [artist.name for artist in track.artists]
        artists = ", ".join(artists_names)
        listen = liblistenbrainz.Listen(
            track_name=track.title, artist_name=artists, listened_at=time
        )
        client.submit_single_listen(listen)

    def health_check(self):
        return super().health_check()
