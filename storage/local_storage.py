import mutagen.mp4
from storage.base import Storage
from pathlib import Path
from shutil import disk_usage, move
import os
import mutagen
import re
from PIL import Image
from PIL.ExifTags import Base
from PIL.PngImagePlugin import PngInfo


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
        norm_path = self._fix_windows_path(path)
        if Path(norm_path).exists():
            return norm_path

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
        artist_name = (track_metadata.get("artist") or ["Unknown"])[0]
        album_title = (track_metadata.get("album") or [None])[0]
        length = int(track_metadata.info.length * 1000)
        del track_metadata
        return {
            "title": title,
            "artist": artist_name,
            "album": album_title,
            "length": length,
        }

    def get_clip_metadata(self, path):
        print(path)
        clip_metadata = mutagen.mp4.MP4(Path(self._fix_windows_path(path)))
        title = clip_metadata.get("\xa9nam")
        artist = clip_metadata.get("\xa9ART")
        album = clip_metadata.get("\xa9alb")
        video_type = clip_metadata.get("stik")
        return {"title": title, "artist": artist, "album": album}

    def write_clip_metadata(self, artist, album, title, path):
        clip_metadata = mutagen.mp4.MP4(Path(self._fix_windows_path(path)))
        clip_metadata["\xa9nam"] = title
        clip_metadata["\xa9ART"] = artist
        clip_metadata["\xa9alb"] = album
        clip_metadata["stik"] = 6

    def get_cover_metadata(self, path):
        norm_path = Path(self._fix_windows_path(path))
        try:
            with Image.open(norm_path) as img:
                if norm_path.suffix == ".png":
                    img.load()
                    return img.info.get("contentId")
                else:
                    exif = img.getexif()
                    return exif.get(Base.UserComment)
        except:
            None

    def write_cover_metadata(self, path, id):
        norm_path = Path(self._fix_windows_path(path))
        img = Image.open(norm_path)
        if norm_path.suffix == ".png":
            img.load()
            pnginfo = PngInfo()
            for key, value in img.info.items():
                if isinstance(value, (str, int, float, bytes)):
                    pnginfo.add_text(str(key), str(value))
            img.save(norm_path, pnginfo=pnginfo)
        else:
            exif = img.getexif()
            exif[Base.UserComment] = id
            img.save(norm_path, exif=exif)

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
