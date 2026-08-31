from core.services import (
    album_service,
    artist_service,
    playlist_service,
    server_service,
    track_service,
    user_service,
)


class SearchesManager:
    def __init__(self):
        self.search_engines, self.start_errors.search = load_modules(
            self.config.get("search", {}), import_modules("search", BaseSearch)
        )

    def global_search(self, query: str) -> SearchResults:
        search_results = SearchResults(artists=[], albums=[], tracks=[])
        for engine in self.search_engines:
            search_engine = engine.instance

            res = search_engine.search_tracks(query)
            if res:
                for item in res:
                    item.external_id = f"{search_engine.TAG}-{item.external_id}"
                search_results.tracks.extend(res)

            res = search_engine.search_albums(query)
            if res:
                for item in res:
                    item.external_id = f"{search_engine.TAG}-{item.external_id}"
                search_results.albums.extend(res)

            res = search_engine.search_artists(query)
            if res:
                for item in res:
                    item.external_id = f"{search_engine.TAG}-{item.external_id}"
                search_results.artists.extend(res)

        with self.db_manager.get_session() as session:
            for artist in search_results.artists:
                db_artist = self.db_manager.get_artist_by_name(session, artist.name)
                artist.id = db_artist.id if db_artist else None
            for album in search_results.albums:
                db_album = self.db_manager.get_album_by_name(session, album.title)
                album.id = db_album.id if db_album else None
            for track in search_results.tracks:
                db_track = self.db_manager.get_track_by_name(session, track.title)
                track.id = db_track.id if not isinstance(db_track, BaseError) else None
        return search_results

    @overload
    def get_global_object(
        self, object_type: Literal["track"], object_id: str
    ) -> Track | BaseError: ...
    @overload
    def get_global_object(
        self, object_type: Literal["album"], object_id: str
    ) -> Album | BaseError: ...
    @overload
    def get_global_object(
        self, object_type: Literal["artist"], object_id: str
    ) -> Artist | BaseError: ...

    def get_global_object(
        self, object_type: Literal["track", "album", "artist"], object_id: str
    ):
        parts = object_id.split("-", 1)
        search_tag = parts[0]
        search_id = parts[1]
        for engine in self.search_engines:
            if engine.tag == search_tag:
                search_engine = engine.instance
                if object_type == "track":
                    track = search_engine.get_track(search_id)
                    if isinstance(track, BaseError):
                        return track
                elif object_type == "album":
                    album = search_engine.get_album(search_id)
                    if isinstance(album, BaseError):
                        return album
                    for track in album.tracks:
                        track.external_id = f"{engine.tag}-{track.external_id}"
                    return album
                elif object_type == "artist":
                    artist = search_engine.get_artist(search_id)
                    if isinstance(artist, BaseError):
                        return artist
                    for album in artist.albums:
                        album.external_id = f"{engine.tag}-{album.external_id}"
                    return artist
