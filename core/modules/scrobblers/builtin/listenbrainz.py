from core.modules.scrobblers.base import Scrobbler
from core.schemas.schemas import Artist, Track, ArtistShort, AlbumShort
import liblistenbrainz
import requests
import musicbrainzngs.musicbrainz

musicbrainzngs.set_useragent("YourAppName", "0.1", "https://yourdomain.example/contact")


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

    def get_tracks_recommendations(self, user_token: str, count: int) -> list[Track]:
        client = liblistenbrainz.ListenBrainz()
        resp = requests.get(
            "https://api.listenbrainz.org/1/validate-token",
            headers={"Authorization": f"Token {user_token}"},
            timeout=5,
        )
        resp.raise_for_status()
        token_data = resp.json()
        if not token_data.get("valid"):
            return []
        recommendation = client.get_user_recommendation_recordings(
            username=token_data["user_name"], count=count
        )
        tracks = []
        payload = recommendation.get("payload") or {}
        for item in payload.get("mbids", []):
            result = musicbrainzngs.get_recording_by_id(
                id=item["recording_mbid"],
                includes=["artists", "releases"],
            )

            recording = result.get("recording")
            if recording is None:
                continue

            albums = [
                AlbumShort(title=album["title"]) for album in result.get("releases", [])
            ]
            artists = [
                ArtistShort(name=artist["name"]) for artist in result.get("artists", [])
            ]

            tracks.append(
                Track(
                    title=recording["title"],
                    albums=albums,
                    artists=artists,
                    length=recording.get("length"),
                )
            )

        return tracks

    def get_similiar_artists(self, artist: Artist) -> list[str]:
        artists = musicbrainzngs.search_artists(artist.name, limit=1)
        artist_list = artists.get("artist-list", [])
        if not artist_list:
            return []

        artist_id = artist_list[0]["id"]
        payload = {
            "artist_mbids": artist_id,
            "algorithm": "session_based_days_1825_session_300_contribution_3_threshold_10_limit_100_filter_True_skip_30",
        }
        response = requests.get(
            "https://labs.api.listenbrainz.org/similar-artists/json",
            params=payload,
            timeout=5,
        )
        artists_names = [artist["name"] for artist in response.json()]
        return artists_names

    def health_check(self):
        return super().health_check()
