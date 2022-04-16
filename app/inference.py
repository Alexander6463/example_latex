import json
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from cv2 import cv2
from mmcv import Config
from mmdet.apis import inference_detector, init_detector

from .config import Settings
from .schemas import Predict, Size
from .utils.extraction import extract_boxes_from_result, prepare_response
from .utils.logger_configure import configure_logging
from .utils.minio import MinioDataLoader, NoSuchBucket
from .utils.rendering import RenderImages

settings = Settings()

logger = configure_logging(__name__)

client = MinioDataLoader(
    endpoint=settings.minio_host,
    access_key=settings.minio_access_key,
    secret_key=settings.minio_secret_key,
)


class InferenceService:

    models: Dict[str, "InferenceService"] = {}

    def __init__(
        self,
        name: str,
        data_bucket: str,
        data_file: str,
        config_bucket: str,
        config_file: str,
        device: str,
    ) -> None:
        if not client.bucket_exists(data_bucket) or not client.bucket_exists(
            config_bucket
        ):
            logger.info(
                "Not existing bucket %s or %s", data_bucket, config_bucket
            )
            raise NoSuchBucket

        self.name = name
        self.ready: bool = False
        self.model: Any = None
        self.config: Config
        self.add_model(name, self)
        self.data_bucket = data_bucket
        self.data_file = data_file
        self.config_bucket = config_bucket
        self.config_file = config_file
        self.load(device)

    @classmethod
    def add_model(cls, name: str, model: "InferenceService") -> None:
        cls.models[name] = model

    def load(self, device: str = settings.device) -> None:
        model_path = Path(tempfile.mkdtemp()) / f"{self.name}.pth"
        config_path = Path(tempfile.mkdtemp()) / f"{self.name}.py"

        if self.config_file.endswith(".py"):
            logger.info("Downloading config from %s", self.config_file)
            if not client.download_file_from_minio(
                self.config_bucket, self.config_file, config_path
            ):
                logger.info("No such file %s", self.config_file)
                return
            self.config = Config.fromfile(config_path)
        else:
            logger.info(
                "Wrong path to config: %s/%s",
                self.config_bucket,
                self.config_file,
            )
            return
        if self.data_file.endswith(".pth"):
            logger.info("Downloading model from %s", self.data_file)
            if not client.download_file_from_minio(
                self.data_bucket, self.data_file, model_path
            ):
                logger.info("No such file %s", self.data_file)
                return
        else:
            logger.info(
                "Wrong path to checkpoint: %s/%s",
                self.data_bucket,
                self.data_file,
            )
            return
        logger.info(
            "Initializing latex inference service with config: %s and model: %s",
            config_path,
            model_path,
        )
        self.model = init_detector(self.config, str(model_path), device)
        self.ready = True

    def predict(self, request: Predict) -> Optional[Dict[str, Dict[str, Any]]]:

        request.output_bucket = (
            request.output_bucket if request.output_bucket else request.bucket
        )
        if not client.bucket_exists(request.bucket):
            logger.info(
                "Wrong way to images: %s does not exist", request.bucket
            )
            return None
        if not client.bucket_exists(request.output_bucket):
            client.make_bucket(request.output_bucket)

        if request.file.endswith(".pdf"):
            res = self.predict_for_pdf(request=request)
        else:
            res = self.predict_for_image(request=request)
        return prepare_response(res)

    def predict_for_pdf(self, request: Predict) -> List[Any]:
        inference_results: List[Any] = []
        render_instance = RenderImages(
            dpi=settings.dpi,
            image_format=settings.image_format,
            minio_client=client,
        )
        sizes: Dict[int, Size] = render_instance.get_size_pages(
            file=request.file, bucket=request.bucket, pages=request.pages  # type: ignore
        )
        images = render_instance.render(
            bucket=request.bucket,
            file=request.file,
            pages=request.pages,  # type: ignore
        )
        for img, page in zip(images, sizes):
            inference_results.append(
                self.get_boxes_from_image(
                    bucket=request.bucket,
                    img=img,
                    page=page,
                    size=sizes[page],
                    verbose=request.args.verbose if request.args else False,
                )
            )
        self.save_results_on_minio(
            request=request, inference_results=inference_results
        )
        return inference_results

    def predict_for_image(self, request: Predict) -> List[Any]:
        inference_results: List[Any] = []
        inference_results.append(
            self.get_boxes_from_image(
                bucket=request.bucket,
                img=request.file,
                verbose=request.args.verbose if request.args else False,
            )
        )
        self.save_results_on_minio(
            request=request, inference_results=inference_results
        )
        return inference_results

    def get_boxes_from_image(
        self,
        bucket: str,
        img: str,
        page: Optional[int] = 1,
        size: Optional[Size] = None,
        verbose: bool = False,
    ) -> Dict[str, Any]:
        logger.info("Extracting boxes from: %s", img)
        local_img = str(
            Path(tempfile.mkdtemp())
            / f"{uuid.uuid4()}.{settings.image_format}"
        )
        client.fget_object(bucket, img, local_img)
        detection = inference_detector(self.model, local_img)
        logger.info(f"verbose {verbose}")
        if verbose:
            img_verbose = self.model.show_result(
                local_img,
                detection,
                score_thr=settings.default_thresholds,
                show=False,
            )
            local_img_verbose = str(
                Path(tempfile.mkdtemp())
                / f"{uuid.uuid4()}.{settings.image_format}"
            )
            cv2.imwrite(local_img_verbose, img_verbose)
            if size:
                img_path = img.replace(
                    f"images_{settings.dpi}", "verbose_latex"
                )
            else:
                img_path = str(
                    Path(img).parent
                    / "verbose_latex"
                    / f"1.{settings.image_format}"
                )
            logger.info("Save image with bboxes to %s", img_path)
            client.fput_object(
                bucket,
                img_path,
                local_img_verbose,
            )
        if not size:
            image = cv2.imread(local_img)
            height, width, _channels = image.shape
            size = Size(width=width, height=height)
            prediction = extract_boxes_from_result(
                result=detection,
                classes=self.model.CLASSES,
                score_thr=settings.default_thresholds,
                size=size.dict(),
                document=False,
            )
        else:
            prediction = extract_boxes_from_result(
                result=detection,
                classes=self.model.CLASSES,
                page_number=page,
                score_thr=settings.default_thresholds,
                size=size.dict(),
                document=True,
            )
        return prediction

    @staticmethod
    def save_results_on_minio(
        request: Predict, inference_results: List[Any]
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / Path(f"{uuid.uuid4()}.json")
            file_path.write_text(json.dumps({"pages": inference_results}))
            client.fput_object(
                request.output_bucket, request.output_path, file_path
            )
