import tempfile
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Dict, List, Union

import pdfplumber

from app.schemas import Size
from app.utils.logger_configure import configure_logging
from app.utils.minio import MinioDataLoader

logger = configure_logging(__file__)


class RenderImages:
    """Used for rendering images with parametrize DPI and format"""

    def __init__(
        self, dpi: int, image_format: str, minio_client: MinioDataLoader
    ) -> None:
        self.dpi = dpi
        self.image_format = image_format
        self.client = minio_client
        self.file_dir = ""
        self.file_name = ""
        self.size_pages = Dict[int, Size]

    def check_pages_in_minio(
        self, bucket: str, file: str, pages: List[int]
    ) -> List[int]:
        """Check images from pdf on minio"""

        if "/" in file:
            self.file_dir, self.file_name = file.rsplit("/", 1)
        else:
            self.file_dir = ""
            self.file_name = file
        self.file_dir = f"{self.file_dir}/images_{self.dpi}"
        minio_pages = [
            element.object_name
            for element in self.client.list_objects(
                bucket, prefix=self.file_dir, recursive=True
            )
        ]
        return list(
            filter(
                lambda x: f"{self.file_dir}/{self.name_image(x)}"
                not in minio_pages,
                pages,
            )
        )

    def render(self, bucket: str, file: str, pages: List[int]) -> List[str]:
        """Rendering images from pdf"""

        dir_with_images = TemporaryDirectory()
        pages_after_check = self.check_pages_in_minio(bucket, file, pages)
        self.client.download_file_from_minio(
            bucket, file, Path(dir_with_images.name) / self.file_name
        )

        if pages_after_check:
            logger.info(
                "Start rendering images from file %s for pages %s",
                file,
                pages,
            )
            with pdfplumber.open(
                Path(dir_with_images.name) / self.file_name
            ) as pdf:
                for page_number in pages_after_check:
                    page = pdf.pages[page_number - 1]
                    img = page.to_image(resolution=self.dpi)
                    filename = Path(dir_with_images.name) / self.name_image(
                        page_number
                    )
                    img.save(filename, format=self.image_format)
            (Path(dir_with_images.name) / self.file_name).unlink()
            self.client.upload_files_to_minio(
                dir_with_images.name, bucket, self.file_dir
            )
            dir_with_images.cleanup()

        return [f"{self.file_dir}/{x}.{self.image_format}" for x in pages]

    def get_size_pages(
        self, file: Union[str, Path], bucket: str, pages: List[int]
    ) -> Dict[int, Size]:
        tmp_path = Path(tempfile.mkdtemp()) / "document.pdf"
        self.client.fget_object(bucket, file, str(tmp_path))
        with pdfplumber.open(tmp_path) as f:
            sizes = dict.fromkeys(pages)
            res = {
                page.page_number: Size(width=page.width, height=page.height)
                for page in f.pages
                if page.page_number in sizes
            }
        return res

    def name_image(self, page_number: int) -> str:
        """Create name of image in format 1.png"""

        return f"{page_number}.{self.image_format}"
