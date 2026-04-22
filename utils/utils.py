from pathlib import Path
from mutagen import File
from mutagen.mp3 import MP3
from mutagen.flac import FLAC, Picture
from mutagen.oggvorbis import OggVorbis
from mutagen.oggopus import OggOpus
import mutagen.mp4
from mutagen.mp4 import MP4
import base64
from storage.base import Storage
import mutagen
import requests
import re
from core.loader import StorageEntry
from core.schemas.schemas import Track
from PIL import Image
from PIL.ExifTags import Base
from PIL.PngImagePlugin import PngInfo


def analyze_lrc(lines: list[str]):
    artist: str = ""
    album: str = ""
    title: str = ""
    offset: int = 0
    text_list = []
    for line in lines:
        content = re.search(r"\[([^\]]+)\]", line)
        if content is None:
            continue
        text = content.group(1)
        time = re.search(r"^(\d{2}):(\d{2}).(\d{2})$", text)
        if "ar" in text:
            artist = _get_tag_value(text)
        elif "al" in text:
            album = _get_tag_value(text)
        elif "ti" in text:
            title = _get_tag_value(text)
        elif "offset" in text:
            offset = _get_tag_value(text)
        elif time:
            mil_time = 0
            text_line = line[time.end() + 2 :].strip()
            mil_time += int(time.group(3))
            mil_time += int(time.group(2)) * 1000
            mil_time += int(time.group(1)) * 60 * 1000
            text_list.append({"time": mil_time, "text": text_line})
    return {
        "artist": artist,
        "album": album,
        "title": title,
        "offset": int(offset),
        "text": text_list,
    }


def _get_tag_value(text: str):
    return text.split(":")[1].strip()


def compare_tracks(original_metadata: dict, track_metadata: dict):
    similarity = 0
    if any(
        orig.lower() in track.lower()
        for orig in original_metadata["title"]
        for track in track_metadata["title"]
    ):
        similarity += 0.5
    if any(
        orig.lower() in track.lower()
        for orig in original_metadata["artist"]
        for track in track_metadata["artist"]
    ):
        similarity += 0.35
    if track_metadata["length"] in original_metadata["length"]:
        similarity += 0.15
    return similarity


def find_best_track(
    searched_tracks: list[Track],
):
    frequent_title: list[list] = []
    frequent_artists: list[list] = []
    frequent_length = []
    for track in searched_tracks:
        title_added = False
        for artist in track.artists:
            artist_added = False
            for i in range(0, len(frequent_artists)):
                if frequent_artists[i][0].lower() == artist.name.lower():
                    frequent_artists[i].append(artist.name.lower())
                    artist_added = True
                    break
            if artist_added == False:
                frequent_artists.append([artist.name.lower()])
        for i in range(0, len(frequent_title)):
            if frequent_title[i][0].lower() == track.title.lower():
                frequent_title[i].append(track.title.lower())
                title_added = True
                break
        if title_added == False:
            frequent_title.append([track.title.lower()])
        frequent_length.append(track.length)
    best_match_title = list(
        sorted(frequent_title, key=lambda titles: len(titles), reverse=True)
    )
    best_match_artist = list(
        sorted(frequent_artists, key=lambda artists: len(artists), reverse=True)
    )
    track = []
    for t in best_match_title[:5]:
        track.append(t[0])
    artist = []
    for a in best_match_artist[:5]:
        artist.append(a[0])
    best_match_track = {"title": track, "artist": artist, "length": frequent_length}
    return best_match_track


def find_best_storage(storages: list[StorageEntry], file_size: int) -> Storage:
    for storage in storages:
        params = storage.params.copy()
        params.update({"id": storage.id, "name": storage.name})
        current_storage = storage.instance
        free_storage = current_storage.check_storage()
        if free_storage > file_size:
            return current_storage


def analyze_track(track_path: Path, default_name: str):
    track_metadata = mutagen.File(track_path, easy=True)
    title = (track_metadata.get("title") or [default_name])[0]
    artist_name = (track_metadata.get("artist") or ["Unknown"])[0]
    album_title = (track_metadata.get("album") or [None])[0]
    bpm = getattr(track_metadata.info, "bpm", None)
    bitrate = getattr(track_metadata.info, "bitrate", None)
    length = int(getattr(track_metadata.info, "length", 0) * 1000)
    return {
        "title": title,
        "artist": [artist_name],
        "album": album_title,
        "bpm": bpm,
        "bitrate": bitrate,
        "length": length,
    }


def full_track_save(best_storage: Storage, dst, saving_path):
    cover = get_cover(dst)
    if cover is not None:
        bytes, ext = cover
        cover_path = dst.parent / f"cover.{ext}"
        cover_path.write_bytes(bytes)
        cover_save_path = saving_path.parent / cover_path.name
        cover_storage_path = best_storage.save_file(cover_path, cover_save_path)
    saved_path = best_storage.save_file(dst, saving_path)
    return {"cover_path": cover_storage_path, "track_path": saved_path}


def save_url_file(url: str, dst: Path):
    with requests.get(url, stream=True) as response:
        response.raise_for_status()
        with open(dst, "wb") as file:
            for chunk in response.iter_content(chunk_size=16384):
                if chunk:
                    file.write(chunk)


def get_cover(filepath: str | Path) -> tuple[bytes, str] | None:
    try:
        audio = File(str(filepath))

        if audio is None:
            return None

        if isinstance(audio, MP3) and audio.tags:
            for key, tag in audio.tags.items():
                if key.startswith("APIC"):
                    return tag.data, tag.split("/")[1]

        if isinstance(audio, FLAC) and audio.pictures:
            pic = audio.pictures[0]
            return pic.data, pic.mime.split("/")[1]

        if isinstance(audio, (OggVorbis, OggOpus)):
            for b64 in audio.get("metadata_block_picture", []):
                pic = Picture(base64.b64decode(b64))
                return pic.data, pic.mime.split("/")[1]

        if isinstance(audio, MP4) and audio.tags:
            covers = audio.tags.get("covr", [])
            if covers:
                mime = "image/jpeg" if covers[0].imageformat == 13 else "image/png"
                return bytes(covers[0]), mime.split("/")[1]

        return None
    except:
        return None


def image_mime(data: bytes) -> str:
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    if data[:2] in (b"BM",):
        return "image/bmp"
    return "application/octet-stream"


def get_track_metadata(path: str) -> dict:
    track_metadata = mutagen.File(Path(path), easy=True)
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


def get_video_metadata(path: str) -> dict:
    video_metadata = MP4(Path(path))
    title = video_metadata.get("\xa9nam")
    artist = video_metadata.get("\xa9ART")
    album = video_metadata.get("\xa9alb")
    video_type = video_metadata.get("stik")
    return {"title": title, "artist": artist, "album": album}


def write_video_metadata(self, artist: str, album: str, title: str, path: str):
    video_metadata = MP4(Path(path))
    video_metadata["\xa9nam"] = title
    video_metadata["\xa9ART"] = artist
    video_metadata["\xa9alb"] = album
    video_metadata["stik"] = 6


def get_cover_metadata(path: str):
    norm_path = Path(path)
    try:
        with Image.open(norm_path) as img:
            if norm_path.suffix == ".png":
                img.load()
                return img.info.get("contentId")
            else:
                exif = img.getexif()
                return exif.get(Base.UserComment)
    except:
        return None


def write_cover_metadata(path: str, id: str):
    norm_path = Path(path)
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
