from fastapi import FastAPI

from src.api import openapi_tags, configure_api, lifespan
from src.logging import LogLevels, configure_logging
from src.config import settings

configure_logging(LogLevels.info)

app = FastAPI(
    openapi_tags=openapi_tags,
    debug=settings.is_development,
    lifespan=lifespan
)

configure_api(app)