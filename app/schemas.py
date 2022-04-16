from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator


class Args(BaseModel):
    verbose: bool = Field(
        example=["false"],
    )


class Predict(BaseModel):
    input_path: str = Field(
        title="Path to the input data",
        description="Latex detector doesn't use this parameter"
        " but it should be provided for the other steps.",
        example="runs/jobId/fileId/previousStepId",
    )
    input: Dict[str, List[int]] = Field(
        title="Input",
        description="Latex detector doesn't use this parameter"
        " but it should be provided for the other steps.",
        example={"1": [2, 5], "3": [2]},
    )
    file: str = Field(
        title="File name",
        description="The full path to the pdf/png-file with extension (without bucket)",
        example="test.pdf",
    )
    bucket: str = Field(
        title="Input bucket name",
        description="The name of the bucket where the pdf/png-file is located",
        example="test",
    )
    pages: Optional[List[int]] = Field(
        title="Page numbers",
        description="The page numbers of the pdf-file that should be used to pedict."
        " Pages parameter is mandatory for multipage documents (e.g. pdf)."
        " It should be provided, even if all pages in document should be processed.",
        example=[1, 5],
    )
    output_path: str = Field(
        title="Output path",
        description="The path inside output bucket where json with prediction will be put. "
        "Should be full path to json with extension.",
        example="runs/jobId/fileId/currentStepId",
    )
    output_bucket: Optional[str] = Field(
        title="Outut bucket name",
        description="The name of the bucket where json with prediction will be put."
        " If it is not specified, then 'bucket' should be used for both 'input_path',"
        " 'file' and 'output_path'.",
        example="result",
        default=None,
    )
    args: Optional[Args] = Field(
        description="If verbose true then model will save image with bboxes",
        default={"verbose": True},
    )

    # pylint: disable=no-self-argument
    @validator("file")
    def file_should_be_pdf_or_image(cls, name: str) -> str:
        if not name.endswith((".pdf", ".png", ".jpg", ".jpeg")):
            raise ValueError("file should be pdf or png")
        return name

    @validator("pages")
    def pages_must_be_set_if_file_pdf(
        cls, pages: List[int], values: Dict[str, Any]
    ) -> List[int]:
        if values.get("file").endswith(".pdf"):  # type: ignore
            if not pages:
                raise ValueError("Set pages for pdf file")
        return pages

    # pylint: disable=no-self-argument
    @validator("output_path")
    def output_should_be_with_json_extension(cls, name: str) -> str:
        if not name.endswith(".json"):
            raise ValueError("output_path should be path to json file")
        return name


class ResponseIsReady(BaseModel):
    is_ready: bool = Field(example=True)


class WrongResponseIsReady(BaseModel):
    detail: str = Field(example="Not existing model")


class ResponsePredict(BaseModel):
    table: Dict[str, List[str]] = Field(
        example={
            "9": [
                "bb1a398a-7cc2-4711-83c2-ad6ca0f18780",
                "0f754874-d0b5-4baa-b374-5717627288db",
            ],
            "10": [
                "ce83e2ca-5540-4aab-bf00-016ec47291f2",
                "db76ae4c-9128-463d-8ccc-6118ff54224e",
            ],
        }
    )


class WrongResponsePredict(BaseModel):
    detail: str = Field(example="Wrong page number")


class ResponsePredictModelIsNotReady(BaseModel):
    status: str = Field(example="Model isn't ready")


class ResponseUpload(BaseModel):
    model_name: str = Field(example="model is loaded")


class WrongResponseUpload(BaseModel):
    detail: str = Field(
        example="Such files don't exist: bucket/folder/test.pth, "
        "bucket/folder/config.py"
    )


class Size(BaseModel):
    width: float
    height: float
