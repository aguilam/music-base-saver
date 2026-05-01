from search.base import Search
import itunespy
from core.schemas.schemas import Track, Album, Artist, ArtistShort


class iTunes(Search):
    TAG = "ITS"

    def __init__(self, config):
        self.config = config

    def search_tracks(self, query: str):
        tracks = itunespy.search_track(query, country="RU")
        normalized_tracks: list[Track] = []
        for track in tracks:
            id = track.track_id
            title = track.track_name
            album = track.collection_name
            artist = [track.artist_name]
            length = int(track.track_time) / 1000
            cover_url = getattr(track, "artwork_url_100", None)
            normalized_tracks.append(
                Track(
                    external_id=id,
                    title=title,
                    length=length,
                    cover_path=cover_url,
                    artists=[ArtistShort(name=artist)],
                    album=Album(title=album),
                )
            )
        return normalized_tracks

    def search_albums(self, query: str):
        albums = itunespy.search_album(query, country="RU")
        normalized_albums: list[Album] = []
        for album in albums:
            id = album.collection_id
            title = album.collection_name
            artist = album.artist_name
            cover_url = getattr(album, "artwork_url_100", None).replace(
                "100x100", "600x600"
            )
            normalized_albums.append(
                Album(
                    external_id=id,
                    title=title,
                    artist=Artist(name=artist),
                    cover_path=cover_url,
                )
            )
        return normalized_albums

    def search_artists(self, query: str):
        artists = itunespy.search_artist(query, country="RU")
        normalized_artists: list[Artist] = []
        for artist in artists:
            id = artist.artist_id
            name = artist.artist_name
            normalized_artists.append(
                Artist(external_id=id, name=name, cover_path=None)
            )
        return normalized_artists

    def get_track(self, id: str):
        track = itunespy.lookup_track(id=id, country="RU")[0]
        return {
            "id": track.track_id,
            "title": track.track_name,
            "artist": [track.artist_name],
            "album": track.collection_name,
            "length": int(track.track_time) / 1000,
            "cover_url": getattr(track, "artwork_url_100", None),
        }

    def get_album(self, id: str):
        album = itunespy.lookup_album(id=id, country="RU")[0]
        title = (album.collection_name,)
        artist = (album.artist_name,)
        cover_url = (
            getattr(album, "artwork_url_100", None).replace("100x100", "600x600"),
        )
        duration = (int(album.get_album_time() * 60),)
        album_tracks = []
        for track in album.get_tracks():
            id = track.track_id
            title = track.track_name
            album_name = track.collection_name
            artist = [track.artist_name]
            length = int(track.track_time) / 1000
            cover_url = getattr(track, "artwork_url_100", None)
            album_tracks.append(
                Track(
                    id=id,
                    title=title,
                    artists=[Artist(name=artist)],
                    album=Album(title=album_name),
                    length=length,
                    cover_path=cover_url,
                )
            )
        return {
            Album(
                external_id=id,
                title=title,
                artist=Artist(name=artist),
                cover_path=cover_url,
                duration=duration,
                tracks=album_tracks,
            )
        }

    def get_artist(self, id: str):
        artist = itunespy.lookup_artist(id=id, country="RU")[0]
        artist_id = (artist.artist_id,)
        name = (artist.artist_name,)
        avatar_url = (artist_albums[0]["cover_url"],)
        artist_albums = []
        for album in artist.get_albums():
            album_id = album.collection_id
            title = album.collection_name
            artist_name = album.artist_name
            cover_url = getattr(album, "artwork_url_100", None).replace(
                "100x100", "600x600"
            )
            artist_albums.append(
                Album(
                    external_id=album_id,
                    title=title,
                    cover_path=cover_url,
                    artist=Artist(name=artist_name),
                )
            )
        return Artist(external_id=artist_id, name=name, cover_path=avatar_url)

    def health_check(self):
        return super().health_check()
