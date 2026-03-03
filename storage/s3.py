from storage.base import Storage
import boto3
from pathlib import Path
import os


class S3(Storage):
    TAG = "S3"

    def __init__(self, config):
        super().__init__(config)
        self.id = config["id"]
        self.name = config["name"]
        endpoint_url = self.config["endpoint_url"]
        access_key_id = self.config["access_key_id"]
        secret_acess_key = self.config["secret_acess_key"]
        self.bucket = self.config["bucket"]
        self.s3 = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_acess_key,
        )

    def save_track(self, file: Path, saving_path: Path) -> str:
        self.s3.upload_file(str(file), self.bucket, str(saving_path))
        os.remove(file)
        return str(saving_path)

    def delete_track(self, track_id: str) -> bool:
        try:
            self.s3.delete_object(Bucket=self.bucket, Key=track_id)
            return True
        except Exception as e:
            print(f"Error deleting S3 object: {e}")
            return False

    def check_storage(self) -> int:

        return 1024 * 1024 * 1024 * 1024

    def get_track(self, track_id: str):
        filename = str(track_id.split("/")[-1])
        dest_path = Path("temp_tracks") / filename
        self.s3.download_file(self.bucket, track_id, str(dest_path))
        return dest_path

    def stream_track(self, path: str, start: int, end: int):
        response = self.s3.get_object(
            Bucket=self.bucket, Key=path, Range=f"bytes={start}-{end}"
        )
        data = response["Body"].read()

        content_range = response.get("ContentRange", "")
        if "/" in content_range:
            total_size = int(content_range.split("/")[-1])
        else:
            total_size = start + len(data)

        return {
            "bytes": data,
            "end_bytes": start + len(data) - 1,
            "file_size": total_size,
        }
