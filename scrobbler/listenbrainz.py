from scrobbler.base import Scrobbler
from core.schemas.schemas import Track
import liblistenbrainz


class ListenBrainz(Scrobbler):
    TAG = "LBZ"

    def __init__(self, config):
        self.config = config
        self.client = liblistenbrainz.ListenBrainz()
        self.client.set_auth_token(config.get("token", ""))

    def post_playing_now(self, track: Track):
        artists_names = [artist.name for artist in track.artists]
        artists = ", ".join(artists_names)
        listen = liblistenbrainz.Listen(track_name=track.title, artist_name=artists)
        self.client.submit_playing_now(listen)

    def submit_listen(self, track: Track, time: int | None):
        artists_names = [artist.name for artist in track.artists]
        artists = ", ".join(artists_names)
        listen = liblistenbrainz.Listen(
            track_name=track.title, artist_name=artists, listened_at=time
        )
        self.client.submit_single_listen(listen)
