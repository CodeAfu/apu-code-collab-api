from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.auth.controller import auth_router
from src.config import settings
from src.database.core import init_db
from src.github.controller import github_router
from src.user.controller import user_router

from loguru import logger


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
        logger.debug("Debug LOG")
        logger.info("API is running")
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
