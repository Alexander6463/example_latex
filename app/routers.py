from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Response, status

from .inference import InferenceService
from .schemas import (
    Predict,
    ResponsePredict,
    ResponsePredictModelIsNotReady,
    WrongResponsePredict,
)
from .utils.logger_configure import configure_logging

logger = configure_logging(__name__)

router = APIRouter()


@router.post(
    "/{model_name}:predict",
    responses={
        200: {
            "model": ResponsePredict,
            "description": "The inference is done",
        },
        404: {
            "model": WrongResponsePredict,
            "description": "File doesnt exist or wrong page number in request",
        },
        202: {
            "model": ResponsePredictModelIsNotReady,
            "description": "The model is not ready",
        },
    },
)
def predict(
    model_name: str, request: Predict, response: Response
) -> Dict[str, Any]:
    model = InferenceService.models.get(model_name)
    if not model:
        logger.info("Predict get not existing model_name %s", model_name)
        raise HTTPException(status_code=404, detail="Not existing model")
    if not model.ready:
        logger.info("%s isn't ready", model_name)
        response.status_code = status.HTTP_202_ACCEPTED
        return {"status": "Model isn't ready"}
    try:
        result = model.predict(request)
    except Exception as err:
        raise HTTPException(status_code=404, detail=f"{err}")
    return result  # type: ignore
