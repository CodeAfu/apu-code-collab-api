import os
from dotenv import load_dotenv
from fastapi import FastAPI

from src.api import openapi_tags, configure_api, lifespan
from src.logging import LogLevels, configure_logging

load_dotenv()

env = os.getenv("PYTHON_ENV")

configure_logging(LogLevels.info)

app = FastAPI(
    openapi_tags=openapi_tags,
    debug=env == "development",
    lifespan=lifespan
)

configure_api(app)

@app.get("/health", tags=["Health Checks"])
async def health_check():
    return {
        "message": "API is running",
    }