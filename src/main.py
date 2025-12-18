from fastapi import FastAPI
from loguru import logger

from src.api import configure_api, lifespan, openapi_tags
from src.config import settings
from src.logging import configure_logging


app = FastAPI(
    openapi_tags=openapi_tags, debug=settings.is_development, lifespan=lifespan
)

configure_logging()
configure_api(app)

if settings.is_development:
    logger.info("Running application on development environment")
