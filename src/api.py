from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from src.auth.controller import auth_router
from src.config import settings
from src.database.core import init_db
from src.github.controller import github_router
from src.user.controller import user_router

openapi_tags = [
    {"name": "Users", "description": "User operations"},
    {"name": "Authentication", "description": "Authentication operations"},
    {"name": "GitHub", "description": "GitHub API operations"},
    {"name": "Health Checks", "description": "Application health checks"},
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


def add_routes(app: FastAPI):
    """
    Register application routes and a /health endpoint on the provided FastAPI app.

    Includes the user and authentication routers with OpenAPI tags "Users" and "Authentication",
    and adds a GET /health endpoint under the "Health Checks" tag that returns a simple status message.

    Parameters:
        app (FastAPI): The FastAPI application to attach routers and endpoints to.
    """
    app.include_router(user_router, tags=["Users"])
    app.include_router(auth_router, tags=["Authentication"])
    app.include_router(github_router, tags=["GitHub"])

    @app.get("/health", tags=["Health Checks"])
    async def health_check():
        """
        Return a simple health status payload for the API.

        Returns:
            dict: A JSON-serializable mapping containing "message" with value "API is running".
        """
        logger.debug("Debug log from health check")
        logger.info("Info log from health check")
        logger.warning("Warning log from health check")
        logger.error("Error log from health check")
        return {
            "message": "API is running",
        }


def configure_api(app: FastAPI):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,  # for cookies
        allow_methods=["*"],
        allow_headers=["*"],
    )

    add_routes(app)
