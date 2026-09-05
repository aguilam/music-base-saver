from dataclasses import dataclass


@dataclass(slots=True)
class FileMetadata:
    file_size: int
    filename: str
    file_suffix: str
