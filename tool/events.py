from enum import Enum


class Event(str, Enum):
    NEW_TRACK = "new_track"
    NEW_COVER = "new_cover"
    NEW_LYRICS = "new_lyrics"
    PROCESS_TRACK = "process_track"
