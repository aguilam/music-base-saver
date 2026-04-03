from downloader.base import Downloader
import requests
import uuid
import time
from pathlib import Path
import re
from typing import Callable


class Slskd(Downloader):
    TAG = "SLS"

    def __init__(self, config):
        super().__init__(config)
        self.slskd_api = self.config["api_route"]
        self.slskd_username = self.config["username"]
        self.slskd_password = self.config["password"]
        self.download_path = self.config["download_path"]

    def _auth(self) -> str:
        slskd_api = self.slskd_api
        slskd_username = self.slskd_username
        slskd_password = self.slskd_password
        request = requests.post(
            f"{slskd_api}/api/v0/session",
            json={"username": slskd_username, "password": slskd_password},
        )
        request.raise_for_status()
        return request.json()["token"]

    def search(self, track_name: str) -> list[dict]:
        token = self._auth()
        slskd_api = self.slskd_api
        headers = {"Authorization": f"Bearer {token}"}
        searches_options = {
            "id": str(uuid.uuid4()),
            "searchText": track_name,
        }
        search_post = requests.post(
            f"{slskd_api}/api/v0/searches", json=searches_options, headers=headers
        )
        search_json = search_post.json()

        search_state = False

        while not search_state:
            time.sleep(3)
            search_check = requests.get(
                f"{slskd_api}/api/v0/searches/{search_json["id"]}",
                headers=headers,
            )
            search_check.raise_for_status()
            search_state = search_check.json()["isComplete"]

        search_get = requests.get(
            f"{slskd_api}/api/v0/searches/{search_json["id"]}/responses",
            headers=headers,
        )
        search_get.raise_for_status()
        searchs = search_get.json()
        search_results = []
        audio_extensions = {"mp3", "m4a", "flac", "opus", "ogg", "wav", "ape"}
        for search in searchs:
            if not search.get("hasFreeUploadSlot"):
                continue
            username = search["username"]
            upload_speed = search["uploadSpeed"]
            files = search.get("files") or []
            if not isinstance(files, list):
                continue
            for file in files:
                if file.get("isLocked"):
                    continue
                splitted_filename: list = file.get("filename", "").split("\\")
                file_ext: str = file.get("extension")
                if file_ext.lstrip(".") not in audio_extensions:
                    continue
                title = splitted_filename[-1].rsplit(".", 1)[0]
                artist = (
                    splitted_filename[-3]
                    if len(splitted_filename) > 3
                    else splitted_filename[-2]
                )
                search_results.append(
                    {
                        "id": str(uuid.uuid4())[:6],
                        "username": username,
                        "upload_speed": upload_speed,
                        "bit_rate": file.get("bitRate"),
                        "size": file.get("size"),
                        "filename": file.get("filename"),
                        "title": title,
                        "artist": artist,
                        "length": (file.get("length") or 0),
                        "extension": file_ext,
                    }
                )

        return search_results

    def check_progress(self, username: str, id: str) -> bool:
        token = self._auth()
        headers = {"Authorization": f"Bearer {token}"}
        slskd_api = self.slskd_api
        download_progress = requests.get(
            f"{slskd_api}/api/v0/transfers/downloads/{username}/{id}",
            headers=headers,
        )
        return download_progress.json()["percentComplete"]

    def download(self, track, progress_callback: Callable[[int], None]):
        token = self._auth()
        slskd_api = self.slskd_api
        headers = {"Authorization": f"Bearer {token}"}
        download_options = [
            {
                "filename": track["filename"],
                "size": track["size"],
            }
        ]
        download = requests.post(
            f"{slskd_api}/api/v0/transfers/downloads/{track["username"]}",
            json=download_options,
            headers=headers,
        )
        download_json = download.json()

        filename = download_json["enqueued"][0]["filename"]
        parts = re.split(r"\\+", filename)
        download_procent = 0
        while download_procent < 100:
            time.sleep(1)

            download_procent = self.check_progress(
                track["username"], download_json["enqueued"][0]["id"]
            )
            progress_callback(download_procent)

        file_path = Path(self.download_path) / parts[-2] / parts[-1]
        return file_path
