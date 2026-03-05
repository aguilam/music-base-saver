from pathlib import Path
from mutagen import File
from mutagen.mp3 import MP3
from mutagen.flac import FLAC, Picture
from mutagen.oggvorbis import OggVorbis
from mutagen.oggopus import OggOpus
from mutagen.mp4 import MP4
import base64


def compare_tracks(original_metadata: dict, track_metadata: dict):
    similarity = 0
    if any(
        orig.lower() in track.lower()
        for orig in original_metadata["title"]
        for track in track_metadata["title"]
    ):
        similarity += 0.4
    if track_metadata["title"].split(".")[-1] in ["m4a", "flac", "mp4"]:
        similarity += 0.25
    if any(
        orig.lower() in track.lower()
        for orig in original_metadata["artist"]
        for track in track_metadata["artist"]
    ):
        similarity += 0.3
    if track_metadata["length"] in original_metadata["length"]:
        similarity += 0.15

    return similarity


def find_best_track(
    searched_tracks: list[dict],
):
    frequent_title: list[list] = []
    frequent_artists: list[list] = []
    frequent_length = []
    for track in searched_tracks:
        title_added = False
        for artist in track["artist"]:
            artist_added = False
            for i in range(0, len(frequent_artists)):
                if frequent_artists[i][0].lower() == artist.lower():
                    frequent_artists[i].append(artist.lower())
                    artist_added = True
                    break
            if artist_added == False:
                frequent_artists.append([artist.lower()])
        for i in range(0, len(frequent_title)):
            if frequent_title[i][0].lower() == track["title"].lower():
                frequent_title[i].append(track["title"].lower())
                title_added = True
                break
        if title_added == False:
            frequent_title.append([track["title"].lower()])
        frequent_length.append(track["length"])
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


def get_cover(filepath: str | Path) -> tuple[bytes, str] | None:

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
