from abc import ABC, abstractmethod


class Importer(ABC):

    @abstractmethod
    @classmethod
    def TAG(cls) -> str:
        pass

    def __init__(self, config):
        self.config = config

    @abstractmethod
    def get_favorited(self):
        pass

    @abstractmethod
    def get_track(self):
        pass

    @abstractmethod
    def get_album(self):
        pass

    @abstractmethod
    def get_artist(self):
        pass

    @abstractmethod
    def get_playlists(self):
        pass

    @abstractmethod
    def get_playlist(self):
        pass

    @abstractmethod
    def get_album_cover(self):
        pass

    @abstractmethod
    def get_artist_cover(self):
        pass

    @abstractmethod
    def get_playlist_cover(self):
        pass

    @abstractmethod
    def get_track_download(self):
        pass

    @abstractmethod
    def get_lyrics(self):
        pass
