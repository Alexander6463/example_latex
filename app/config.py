from pathlib import Path

from pydantic import BaseSettings


class Settings(BaseSettings):
    minio_host: str = "minio:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    default_thresholds: float = 0.3
    dpi: int = 300
    inch_to_point: int = 72
    image_format: str = "png"
    data_bucket: str = "test"
    data_file: str = "latex-detector.pth"
    config_bucket: str = "test"
    config_file: str = "latex-detector.py"
    model_name: str = "latex-detector"
    device: str = "cpu"
    host: str = "0.0.0.0"
    port: int = 8000
    log_file: str = str(Path(__file__).parent.joinpath("inference.log"))
