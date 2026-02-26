from search.base import Search
from core.schemas import Track
import itunespy


class iTunes(Search):
    TAG = "ITS"

    def __init__(self, config):
        self.config = config

    def search_tracks(self, query: str) -> list[Track]:
        tracks = itunespy.search_track(query, country="RU")
        normalized_tracks: list[Track] = []
        for track in tracks:
            title = track.track_name
            artist = [track.artist_name]
            length = int(track.track_time)
            normalized_tracks.append(
                {"title": title, "artist": artist, "length": length, "source": self.TAG}
            )
        return normalized_tracks

    def search_albums(self, query: str) -> list[dict]:
        albums = itunespy.search_album(query, country="RU")
        return albums

    def search_artists(self, query: str) -> list[dict]:
        artists = itunespy.search_artist(query, country="RU")
        return artists
