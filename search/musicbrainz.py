from search.base import Search
import musicbrainzngs
from core.schemas import Track
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
            artists = [track["artist-credit"][0]["name"]]
            for alias in track["artist-credit"][0]["artist"].get("alias-list", []):
                artists.append(alias.get("alias"))
            normalized_tracks.append(
                {
                    "id": str(uuid.uuid4()),
                    "title": track["title"],
                    "artist": artists,
                    "length": int(track.get("length", 0)),
                    "source": self.TAG,
                }
            )
        return normalized_tracks

    def search_albums(self, query: str) -> list[dict]:
        albums = musicbrainzngs.search_releases(query)

        return albums["release-list"]

    def search_artists(self, query: str) -> list[dict]:
        artists = musicbrainzngs.search_artists(query)

        return artists["artist-list"]
