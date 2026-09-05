from core.modules.storages.schemas import FileMetadata
from core.modules.storages.base import Storage
from pathlib import Path
from shutil import disk_usage, move
import os


class LocalStorage(Storage):
    TAG = "LOC"

    def __init__(self, config):
        super().__init__(config)
        self.save_directory = Path(self.config["save_directory"])
        self.save_directory.mkdir(parents=True, exist_ok=True)

    def save_file(self, file_path: str, saving_path: str) -> str:
        dst = self.save_directory / saving_path
        dst.parent.mkdir(parents=True, exist_ok=True)
        move(file_path, dst)
        return str(dst)

    def delete_file(self, path: str) -> bool:
        try:
            os.remove(path)
            return True
        except Exception:
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

    def get_file_metadata(self, path: str) -> FileMetadata:
        file_path = Path(path)
        file_size = file_path.stat().st_size
        filename = file_path.stem
        file_suffix = file_path.suffix
        return FileMetadata(
            file_size=file_size, filename=filename, file_suffix=file_suffix
        )

    def get_range_bytes(self, path: str, start: int, end: int):
        chunk_size = 64 * 1024
        read_bytes = end - start + 1
        with open(self._fix_windows_path(path), "rb") as file:
            file.seek(start)
            while read_bytes > 0:
                chunk = file.read(min(chunk_size, read_bytes))
                if not chunk:
                    break
                read_bytes -= len(chunk)
                yield chunk

    def health_check(self):
        return super().health_check()

    def _fix_windows_path(self, p: str) -> str:
        drive, rest = os.path.splitdrive(p)

        if ":" in rest:
            rest = rest.replace(":", "\\", 1)

        return drive + rest
