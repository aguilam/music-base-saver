from abc import ABC, abstractmethod
from core.schemas.schemas import (
    ImporterTrack,
    ImporterAlbum,
    ImporterArtist,
    ImporterPlaylist,
)
from core.base_service import Service


class Importer(Service, ABC):
    def __init__(self, config):
        self.config = config

    @abstractmethod
    def get_favorited(
        self,
    ) -> tuple[list[int | str], list[int | str], list[int | str], list[int | str]]:
        pass

    @abstractmethod
    def get_user_playlists(self) -> list[int | str]:
        pass

    @abstractmethod
    def get_artist(self, artist_id: int | str) -> ImporterArtist:
        pass

    @abstractmethod
    def get_playlist(self, playlist_id: int | str) -> ImporterPlaylist:
        pass

    @abstractmethod
    def get_album(self, album_id: int | str) -> ImporterAlbum:
        pass

    @abstractmethod
    def get_track(self, track_id: int | str) -> ImporterTrack:
        pass

    @abstractmethod
    def get_track_download_link(self, track_id: int | str) -> tuple[str, str]:
        pass

    @abstractmethod
    def get_lyrics_download_link(self, track_id: int | str) -> tuple[str, str]:
        pass

    @abstractmethod
    def get_music_video_download_link(self, track_id: int | str) -> tuple[str, str]:
        pass
