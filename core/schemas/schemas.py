from pydantic import BaseModel
from enum import StrEnum


class Track(BaseModel):
    id: str
    title: str
    artist: list[str]
    length: int


class Album(BaseModel):
    id: str


class Artist(BaseModel):
    id: str


class QueryType(StrEnum):
    ALL = "all"
    TRACK = "track"
    ALBUM = "album"
    ARTIST = "artist"
