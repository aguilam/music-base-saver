from storage.base import Storage
from pathlib import Path
from shutil import disk_usage, move
import os
import mutagen
import re


class LocalStorage(Storage):
    TAG = "LOC"

    def __init__(self, config):
        super().__init__(config)
        self.id = config["id"]
        self.name = config["name"]
        self.save_directory = Path(self.config["save_directory"])
        self.save_directory.mkdir(parents=True, exist_ok=True)

    def save_track(self, file: Path, saving_path: Path) -> Path:
        dst = self.save_directory / saving_path
        dst.parent.mkdir(parents=True, exist_ok=True)
        move(file, dst)
        return dst

    def delete_track(path: str) -> bool:
        try:
            os.remove(path)
            return True
        except:
            return False

    def check_storage(self) -> int:
        _, _, free = disk_usage(self.save_directory)
        return free

    def get_track(self, path: str):
        print(path)
        if Path(path).exists():
            return path

    def get_all_tracks_paths(
        self,
    ):
        return [
            f"{f.parent}:{f.name}"
            for f in self.save_directory.rglob("*")
            if f.is_file()
        ]

    def get_track_metadata(self, path):
        track_metadata = mutagen.File(Path(self._fix_windows_path(path)), easy=True)
        title_list = track_metadata.get("title")
        title = title_list[0] if title_list else Path(path).stem
        artist_list = track_metadata.get("artist")
        artist = artist_list if artist_list else ["Unknown"]
        length = int(track_metadata.info.length)
        del track_metadata
        return {"title": title, "artist": artist, "length": length}

    def stream_track(self, path: str, start: int, end: int):
        file_size = os.stat(self._fix_windows_path(path)).st_size
        end_bytes = min(end, file_size - 1)
        read_bytes = end_bytes - start + 1
        with open(self._fix_windows_path(path), "rb") as file:
            file.seek(start)
            bytes = file.read(read_bytes)
            return {
                "bytes": bytes,
                "end_bytes": end_bytes,
                "file_size": file_size,
            }

    def _fix_windows_path(self, p: str) -> str:
        drive, rest = os.path.splitdrive(p)

        if ":" in rest:
            rest = rest.replace(":", "\\", 1)

        return drive + rest
