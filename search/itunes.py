from search.base import Search
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
            length = int(track.track_time) / 1000
            cover_url = getattr(track, "artwork_url_100", None)
            normalized_tracks.append(
                {
                    "id": id,
                    "title": title,
                    "artist": artist,
                    "album": album,
                    "length": length,
                    "cover_url": cover_url,
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
            cover_url = getattr(album, "artwork_url_100", None).replace(
                "100x100", "600x600"
            )
            normalized_albums.append(
                {
                    "id": id,
                    "title": title,
                    "artist": artist,
                    "cover_url": cover_url,
                }
            )
        return normalized_albums

    def search_artists(self, query: str) -> list[dict]:
        artists = itunespy.search_artist(query, country="RU")
        normalized_artists = []
        for artist in artists:
            id = artist.artist_id
            name = artist.artist_name
            normalized_artists.append(
                {
                    "id": id,
                    "name": name,
                    "cover_url": None,
                }
            )
        return normalized_artists

    def get_track(self, id: str) -> list[dict]:
        track = itunespy.lookup_track(id=id, country="RU")[0]
        return {
            "id": track.track_id,
            "title": track.track_name,
            "artist": [track.artist_name],
            "album": track.collection_name,
            "length": int(track.track_time) / 1000,
            "cover_url": getattr(track, "artwork_url_100", None),
        }

    def get_album(self, id: str) -> list[dict]:
        album = itunespy.lookup_album(id=id, country="RU")[0]
        album_tracks = []
        for track in album.get_tracks():
            id = track.track_id
            title = track.track_name
            album_name = track.collection_name
            artist = [track.artist_name]
            length = int(track.track_time) / 1000
            cover_url = getattr(track, "artwork_url_100", None)
            album_tracks.append(
                {
                    "id": id,
                    "title": title,
                    "artist": artist,
                    "album": album_name,
                    "length": length,
                    "cover_url": cover_url,
                }
            )
        return {
            "id": album.collection_id,
            "title": album.collection_name,
            "artist": [album.artist_name],
            "cover_url": getattr(album, "artwork_url_100", None).replace(
                "100x100", "600x600"
            ),
            "duration": int(album.get_album_time() * 60),
            "tracks": album_tracks,
        }

    def get_artist(self, id: str) -> list[dict]:
        artist = itunespy.lookup_artist(id=id, country="RU")[0]
        artist_albums = []
        for album in artist.get_albums():
            id = album.collection_id
            title = album.collection_name
            artist_name = album.artist_name
            cover_url = getattr(album, "artwork_url_100", None).replace(
                "100x100", "600x600"
            )
            artist_albums.append(
                {
                    "id": id,
                    "title": title,
                    "artist": artist_name,
                    "cover_url": cover_url,
                }
            )
        return {
            "id": artist.artist_id,
            "name": artist.artist_name,
            "cover_url": artist_albums[0]["cover_url"],
            "albums": artist_albums,
        }
