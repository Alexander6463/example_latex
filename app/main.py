import uvicorn
from fastapi import FastAPI

from .config import Settings
from .inference import InferenceService
from .routers import router

app = FastAPI(title="Latex detector app")
app.include_router(router)

settings = Settings()


if __name__ == "__main__":
    settings = Settings()
    InferenceService(
        settings.model_name,
        settings.data_bucket,
        settings.data_file,
        settings.config_bucket,
        settings.config_file,
        settings.device,
    )
    uvicorn.run(app, host=settings.host, port=settings.port)
