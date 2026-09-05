from core.modules.storages.base import Storage
from pathlib import Path
from mega import Mega
import os


class MegaStorage(Storage):
    TAG = "MEG"

    def __init__(self, config):
        super().__init__(config)
        self.id = config["id"]
        self.name = config["name"]
        email = self.config["email"]
        password = self.config["password"]
        mega = Mega()
        self.directory = self.config.get("directory", "music_saver")
        self.m = mega.login(email=email, password=password)
        folder = self.m.find(self.directory)
        if not folder:
            self.m.create_folder(self.directory)

    def save_file(self, file_path: Path) -> Path:
        folder = self.m.find(self.directory)
        file = self.m.upload(str(file_path), folder[0])
        os.remove(file_path)
        return file["f"][0]["h"]

    def delete_file(self, link: str) -> bool:
        self.m.destroy(link)
        return True

    def check_storage(self) -> int:
        storage_space = self.m.get_storage_space()
        return storage_space["total"] - storage_space["used"]

    def get_file(self, link: str):
        m = self.m

        files = m.get_files()

        file_info = files.get(link)

        file_tulpe = (link, file_info)

        download_path = self.m.download(file_tulpe, dest_path=str(Path("temp_tracks")))

        return download_path

    def health_check(self):
        return super().health_check()
