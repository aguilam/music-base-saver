from core.modules.searches.base import Search
import itunespy
from core.schemas.schemas import Track, Album, Artist, ArtistShort


class iTunes(Search):
    TAG = "ITS"

    def __init__(self, config):
        self.config = config

    def search_tracks(self, query: str):
        try:
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
        except:
            return []

    def search_albums(self, query: str):
        try:
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
                        artists=[Artist(name=artist)],
                        cover_path=cover_url,
                    )
                )
            return normalized_albums
        except:
            return []

    def search_artists(self, query: str):
        try:
            artists = itunespy.search_artist(query, country="RU")
            normalized_artists: list[Artist] = []
            for artist in artists:
                id = artist.artist_id
                name = artist.artist_name
                normalized_artists.append(
                    Artist(external_id=id, name=name, cover_path=None)
                )
            return normalized_artists
        except:
            return None

    def get_track(self, id: str):
        try:
            track = itunespy.lookup_track(id=id, country="RU")[0]
            return {
                Track(
                    external_id=track.track_id,
                    title=track.track_name,
                    artists=[
                        ArtistShort(external_id=track.artist_id, name=track.artist_name)
                    ],
                    album=Album(
                        external_id=track.collection_id, title=track.collection_name
                    ),
                    length=int(track.track_time) / 1000,
                    cover_path=getattr(track, "artwork_url_100", None),
                )
            }
        except:
            return None

    def get_album(self, id: str):
        try:
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
                        external_id=id,
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
                    artists=[Artist(name=artist)],
                    cover_path=cover_url,
                    duration=duration,
                    tracks=album_tracks,
                )
            }
        except:
            return None

    def get_artist(self, id: str):
        try:
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
                        artists=[Artist(name=artist_name)],
                    )
                )
            return Artist(external_id=artist_id, name=name, cover_path=avatar_url)
        except:
            return None

    def health_check(self):
        return super().health_check()
