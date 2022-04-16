from pathlib import Path
from typing import Union

from minio import Minio

from .logger_configure import configure_logging

LOGGER = configure_logging(__file__)


class NoSuchBucket(Exception):
    pass


class NoSuchKey(Exception):
    pass


class MinioDataLoader(Minio):  # type: ignore
    """Used for upload and download files from Minio"""

    def __init__(
        self, endpoint: str, access_key: str, secret_key: str
    ) -> None:
        super().__init__(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=False,
        )

    def download_file_from_minio(
        self, bucket: str, file: str, output_path: Path
    ) -> bool:
        """Download file from minio"""

        if self.bucket_exists(bucket):
            LOGGER.info("Download file %s from bucket %s", file, bucket)
            try:
                self.fget_object(bucket, file, str(output_path))
            except NoSuchKey:
                LOGGER.info("ResponseError: The specified key does not exist")
                return False
        else:
            LOGGER.info("There isn't file in %s", file)
            return False
        return True

    def upload_files_to_minio(
        self, directory: Union[str, Path], bucket: str, path_in_minio: str
    ) -> bool:
        """Upload dir with files to bucket in minio"""

        if not self.bucket_exists(bucket):
            self.make_bucket(bucket)
        LOGGER.info(
            "Upload files from directory %s to bucket %s", directory, bucket
        )
        try:
            for file in Path(directory).glob("**/*.*"):
                self.fput_object(
                    bucket,
                    str(
                        Path(path_in_minio) / Path(file).relative_to(directory)
                    ),
                    Path(file),
                )
            return True
        except ValueError as e:
            LOGGER.info("Error %s while upload file into minio", e)
            return False
