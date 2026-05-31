from storage.base import Storage
from pathlib import Path
from shutil import disk_usage, move
import os


class LocalStorage(Storage):
    TAG = "LOC"

    def __init__(self, config):
        super().__init__(config)
        self.id = config["id"]
        self.name = config["name"]
        self.save_directory = Path(self.config["save_directory"])
        self.save_directory.mkdir(parents=True, exist_ok=True)

    def save_file(self, file: str, saving_path: str) -> str:
        dst = self.save_directory / saving_path
        dst.parent.mkdir(parents=True, exist_ok=True)
        move(file, dst)
        return str(dst)

    def delete_file(path: str) -> bool:
        try:
            os.remove(path)
            return True
        except:
            return False

    def check_storage(self) -> int:
        _, _, free = disk_usage(self.save_directory)
        return free

    def get_file(self, path: str):
        norm_path = self._fix_windows_path(path)
        if Path(norm_path).exists():
            return norm_path

    def get_all_files_paths(
        self,
    ):
        files = []
        for f in self.save_directory.rglob("*"):
            if f.is_file():
                files.append((str(f), f.name))
        return files

    def get_range_bytes(self, path: str, start: int, end: int):
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

    def health_check(self):
        return super().health_check()

    def _fix_windows_path(self, p: str) -> str:
        drive, rest = os.path.splitdrive(p)

        if ":" in rest:
            rest = rest.replace(":", "\\", 1)

        return drive + rest
