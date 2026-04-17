from search.base import Search
import musicbrainzngs
from core.schemas.schemas import Track, Album, Artist, ArtistShort
import uuid


class MusicBrainz(Search):
    TAG = "MBZ"

    musicbrainzngs.set_useragent(
        "YourAppName", "0.1", "https://yourdomain.example/contact"
    )

    def __init__(self, config):
        self.config = config

    def search_tracks(self, query: str) -> list[Track]:
        tracks = musicbrainzngs.search_recordings(query)
        normalized_tracks = []
        for track in tracks["recording-list"]:
            track_artists = [ArtistShort(name=track["artist-credit"][0]["name"])]
            for alias in track["artist-credit"][0]["artist"].get("alias-list", []):
                track_artists.append(ArtistShort(name=alias.get("alias")))
            normalized_tracks.append(
                Track(
                    external_id=track["id"],
                    title=track["title"],
                    artists=track_artists,
                    length=int(track.get("length", 0)),
                )
            )
        return normalized_tracks

    def search_albums(self, query: str) -> list[Album]:
        albums = musicbrainzngs.search_releases(query)

        return albums["release-list"]

    def search_artists(self, query: str) -> list[Artist]:
        artists = musicbrainzngs.search_artists(query)

        return artists["artist-list"]

    def get_track(self, id: str) -> Track:
        pass

    def get_album(self, id: str) -> Album:
        pass

    def get_artist(self, id: str) -> Artist:
        pass
