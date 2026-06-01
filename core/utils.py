from pathlib import Path
from collections.abc import Mapping
from mutagen import File
import mutagen.flac
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
import pyexiv2
import io
from core.schemas.schemas import TrackMetadata, TrackAlbumMetadata


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
        if text.startswith("ar:"):
            artist = _get_tag_value(text)
        elif text.startswith("al:"):
            album = _get_tag_value(text)
        elif text.startswith("ti:"):
            title = _get_tag_value(text)
        elif text.startswith("offset"):
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
    similarity = 0.0
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


def find_best_storage(storages: list[StorageEntry], file_size: int):
    for storage in storages:
        current_storage = storage.instance
        free_storage = current_storage.check_storage()
        if free_storage > file_size:
            return storage


def get_track_metadata_by_path(track_path: Path):
    track_metadata = mutagen.File(track_path, easy=True)
    return _get_track_metadata(track_metadata)


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


def save_file_from_url(url: str, dst: Path):
    with requests.get(url, stream=True, timeout=(10, 20)) as response:
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


def _clean_track_tag_value(tag) -> str | None:
    while True:
        if tag is None:
            return None

        if isinstance(tag, (list, tuple)):
            tag = next((item for item in tag if item is not None), None)
            continue

        if isinstance(tag, Mapping):
            tag = (
                tag.get('lang="x-default"')
                or tag.get("x-default")
                or next(iter(tag.values()), None)
            )
            continue

        value = tag.strip() if hasattr(tag, "strip") else str(tag).strip()
        return value or None


def _get_clear_track_tag(name_tag: str, metadata):
    return _clean_track_tag_value(metadata.get(name_tag))


def _get_clear_track_tags(name_tag: str, metadata) -> list[str]:
    tags = metadata.get(name_tag, [])
    if not isinstance(tags, (list, tuple)):
        tags = [tags]
    return [value for tag in tags if (value := _clean_track_tag_value(tag)) is not None]


def _get_track_metadata(track_metadata):
    title = _get_clear_track_tag("title", track_metadata)
    artists_names = _get_clear_track_tags("artist", track_metadata)
    album_artist_tag = _get_clear_track_tag("albumartist", track_metadata)
    album_artist = (
        [artist.strip() for artist in album_artist_tag.split(",") if artist.strip()]
        if album_artist_tag
        else artists_names
    )
    album_title = _get_clear_track_tag("album", track_metadata)
    album_position = _get_clear_track_tag("tracknumber", track_metadata)
    disc_number = _get_clear_track_tag("discnumber", track_metadata)
    date = _get_clear_track_tag("date", track_metadata)
    genres = _get_clear_track_tags("genre", track_metadata)
    moods = _get_clear_track_tags("mood", track_metadata)
    length = int(getattr(track_metadata.info, "length", 0) * 1000)
    bpm = getattr(track_metadata.info, "bpm", [None])[0]
    bitrate = getattr(track_metadata.info, "bitrate", None)
    return TrackMetadata(
        title=title,
        artists=artists_names,
        albums=[
            TrackAlbumMetadata(
                title=album_title,
                album_artists=album_artist,
                disc_number=disc_number,
                album_position=album_position,
            )
        ],
        length=length,
        year=date,
        genres=genres,
        moods=moods,
        bitrate=bitrate,
        bpm=bpm,
    )


def get_track_metadata_by_bytes(bytes: bytes):
    track_metadata = mutagen.File(io.BytesIO(bytes), easy=True)
    return _get_track_metadata(track_metadata)


def get_video_metadata(video_bytes: bytes) -> dict:
    video_metadata = MP4(io.BytesIO(video_bytes))
    title = _get_clear_track_tag("\xa9nam", video_metadata)
    artists = _get_clear_track_tag("\xa9ART", video_metadata)
    album = _get_clear_track_tag("\xa9alb", video_metadata)
    video_type = _get_clear_track_tag("stik", video_metadata)
    return {"title": title, "artists": artists, "album": album}


def write_video_metadata(artist: str, album: str, title: str, path: str):
    video_metadata = MP4(Path(path))
    video_metadata["\xa9nam"] = [title]
    video_metadata["\xa9ART"] = [artist]
    video_metadata["\xa9alb"] = [album]
    video_metadata["stik"] = [6]
    video_metadata.save()


def get_cover_metadata(bytes: bytes) -> dict | None:
    try:
        with pyexiv2.ImageData(bytes) as img:
            tags = img.read_xmp()
            return {
                "title": _get_clear_track_tag("Xmp.dc.title", tags),
                "creator": _get_clear_track_tags("Xmp.dc.creator", tags),
                "subject": _get_clear_track_tags("Xmp.dc.subject", tags),
            }
    except Exception:
        return None


def write_cover_metadata(
    path: str,
    album: str | None = None,
    artists: list[str] | None = None,
    genres: list[str] | None = None,
):
    metadata = {}
    if album:
        metadata[f"Xmp.dc.title"] = album
    if artists and len(artists) > 0:
        metadata[f"Xmp.dc.creator"] = artists
    if genres and len(genres) > 0:
        metadata[f"Xmp.dc.subject"] = genres
    with pyexiv2.Image(path) as img:
        img.modify_xmp(metadata)


def write_track_metadata(
    file_path: str, new_metadata: dict[str, list[str]], rewrite: bool = True
):
    track_file = mutagen.File(file_path, easy=True)
    for key, value in new_metadata.items():
        if not rewrite and track_file.get(key):
            continue
        track_file[key] = value
    track_file.save()


def sanitize_filename(filename: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "", filename).strip()


def read_lyrics_text(text: str) -> tuple[str, str | dict]:
    lines = text.splitlines()

    lrc_line_re = re.compile(r"^\s*\[\d{2}:\d{2}\.\d{2,3}\]")

    is_lrc = any(lrc_line_re.match(line) for line in lines)

    if is_lrc:
        return ("lrc", analyze_lrc(lines))
    else:
        return ("txt", text)


def get_id_from_string(string: str, prefix: str = "al|tr|ar|pl"):
    if re.match(rf"^{(prefix)}-\d+$", string):
        parts = string.split("-")
        return (parts[0], int(parts[1]))
    else:
        return None
