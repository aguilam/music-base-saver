import musicbrainzngs.musicbrainz
from search.base import Search
from core.schemas.schemas import Track, Album, Artist, ArtistShort
import pprint


class MusicBrainz(Search):
    TAG = "MBZ"

    musicbrainzngs.set_useragent(
        "YourAppName", "0.1", "https://yourdomain.example/contact"
    )

    def __init__(self, config):
        self.config = config

    def search_tracks(self, query: str):
        tracks = musicbrainzngs.search_recordings(query)
        normalized_tracks = []
        for track in tracks.get("recording-list", []):
            for artist in track.get("artist-credit", []):
                track_artists = []
                if isinstance(artist, dict):
                    track_artists.append(ArtistShort(name=artist["name"]))
            normalized_tracks.append(
                Track(
                    external_id=track["id"],
                    title=track["title"],
                    artists=track_artists,
                    length=int(track.get("length", 0)),
                )
            )
        return normalized_tracks

    def search_albums(self, query: str):
        results = musicbrainzngs.search_releases(query)
        normalized_albums = []
        for album in results.get("release-list", []):
            normalized_artists = []
            for artist in album.get("artist-credit", []):
                if not isinstance(artist, dict):
                    continue
                normalized_artists.append(
                    ArtistShort(
                        name=artist["artist"]["name"],
                        external_id=artist["artist"]["id"],
                    )
                )
            normalized_albums.append(
                Album(
                    external_id=album["id"],
                    title=album["title"],
                    artists=normalized_artists,
                )
            )

        return normalized_albums

    def search_artists(self, query: str):
        result = musicbrainzngs.search_artists(query)
        normalized_artists = []
        for artist in result.get("artist-list", []):
            normalized_artists.append(
                Artist(name=artist["name"], external_id=artist["id"])
            )
        return normalized_artists

    def get_track(self, id: str):
        result = musicbrainzngs.get_recording_by_id(id)
        if result.get("recording", None) is None:
            return None
        track = result["recording"]
        return Track(
            title=track["title"], external_id=track["id"], length=track["length"]
        )

    def get_album(self, id: str):
        result = musicbrainzngs.get_release_by_id(id, includes=["recordings"])
        if result.get("release", None) is None:
            return None
        album = result["release"]
        normalized_tracks = []
        medium_list = album["medium-list"][0]
        for track in medium_list.get("track-list", []):
            normalized_tracks.append(
                Track(
                    external_id=track["recording"]["id"],
                    title=track["recording"]["title"],
                    length=track["recording"]["length"],
                )
            )
        return Album(
            title=album["title"], external_id=album["id"], tracks=normalized_tracks
        )

    def get_artist(self, id: str):
        result = musicbrainzngs.get_artist_by_id(id, includes=["releases"])
        if result.get("artist", None) is None:
            return None
        artist = result["artist"]
        normalized_albums = []
        for album in artist.get("release-list", []):
            normalized_albums.append(
                Album(
                    external_id=album["id"],
                    title=album["title"],
                )
            )
        return Artist(name=artist["name"], external_id=artist["id"])

    def health_check(self):
        return super().health_check()
