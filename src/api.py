from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from src.auth.controller import auth_router
from src.config import settings
from src.database.core import init_db
from src.github.controller import github_router
from src.user.controller import user_router

from src.entities import user, refresh_token  #  noqa: F401

openapi_tags = [
    {"name": "Users", "description": "User operations"},
    {"name": "Authentication", "description": "Authentication operations"},
    {"name": "GitHub OAuth", "description": "GitHub Authorization"},
    {"name": "Health Checks", "description": "Application health checks"},
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


def add_routes(app: FastAPI):
    app.include_router(user_router, tags=["Users"])
    app.include_router(auth_router, tags=["Authentication"])
    app.include_router(github_router, tags=["GitHub OAuth"])

    @app.get("/health", tags=["Health Checks"])
    async def health_check():
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
