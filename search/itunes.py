from search.base import Search
from core.schemas import Track
import itunespy


class iTunes(Search):
    TAG = "ITS"

    def __init__(self, config):
        self.config = config

    def search_tracks(self, query: str) -> list[dict]:
        tracks = itunespy.search_track(query, country="RU")
        normalized_tracks = []
        for track in tracks:
            id = track.track_id
            title = track.track_name
            album = track.collection_name
            artist = [track.artist_name]
            length = int(track.track_time)
            cover_url = getattr(track, "artwork_url_100", None)
            normalized_tracks.append(
                {
                    "id": id,
                    "title": title,
                    "artist": artist,
                    "album": album,
                    "length": length,
                    "cover_url": cover_url,
                    "source": self.TAG,
                }
            )
        return normalized_tracks

    def search_albums(self, query: str) -> list[dict]:
        albums = itunespy.search_album(query, country="RU")
        normalized_albums = []
        for album in albums:
            id = album.collection_id
            title = album.collection_name
            artist = album.artist_name
            cover_url = getattr(album, "artwork_url_100", None)
            normalized_albums.append(
                {
                    "id": id,
                    "title": title,
                    "artist": artist,
                    "cover_url": cover_url,
                    "source": self.TAG,
                }
            )
        return normalized_albums

    def search_artists(self, query: str) -> list[dict]:
        artists = itunespy.search_artist(query, country="RU")
        normalized_artists = []
        for artist in artists:
            id = artist.artist_id
            name = artist.artist_name
            cover_url = getattr(artist, "artwork_url_100", None)
            normalized_artists.append(
                {
                    "id": id,
                    "name": name,
                    "cover_url": cover_url,
                    "source": self.TAG,
                }
            )
        return normalized_artists
